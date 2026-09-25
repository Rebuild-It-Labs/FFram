"""
core/hardware.py - GPU encoder detection for NVENC, QSV, and AMF.
Auto-detects available hardware encoders and provides fallback to CPU.
"""

import subprocess
from functools import lru_cache
from typing import Optional


# Mapping of hardware encoder names to their FFmpeg codec identifiers
HARDWARE_ENCODERS = {
    "h264": {
        "nvenc": "h264_nvenc",
        "qsv": "h264_qsv",
        "amf": "h264_amf",
        "cpu": "libx264",
    },
    "h265": {
        "nvenc": "hevc_nvenc",
        "qsv": "hevc_qsv",
        "amf": "hevc_amf",
        "cpu": "libx265",
    },
}


@lru_cache(maxsize=1)
def detect_available_encoders(ffmpeg_path: str = "ffmpeg") -> list[str]:
    """
    Detect all available FFmpeg encoders by running 'ffmpeg -encoders'.
    Results are cached for the session.
    """
    try:
        result = subprocess.run(
            [ffmpeg_path, "-encoders", "-hide_banner"],
            capture_output=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        if result.returncode == 0:
            stdout_str = result.stdout.decode("utf-8", errors="replace")
            return [
                line.split()[1]
                for line in stdout_str.splitlines()
                if line.strip().startswith("V") or line.strip().startswith("A")
            ]
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
        pass
    return []


def has_encoder(encoder_name: str, ffmpeg_path: str = "ffmpeg") -> bool:
    """Check if a specific encoder is available."""
    return encoder_name in detect_available_encoders(ffmpeg_path)


def get_best_h264_encoder(ffmpeg_path: str = "ffmpeg", prefer: str = "auto") -> str:
    """
    Get the best available H.264 encoder.
    Priority: NVENC > QSV > AMF > libx264 (CPU)
    
    Args:
        ffmpeg_path: Path to FFmpeg.
        prefer: "auto", "gpu", "cpu", "nvenc", "qsv", "amf"
    """
    if prefer == "cpu":
        return "libx264"

    encoders = HARDWARE_ENCODERS["h264"]
    if prefer in encoders and prefer != "cpu":
        if has_encoder(encoders[prefer], ffmpeg_path):
            return encoders[prefer]

    # Auto priority order
    for hw in ["nvenc", "qsv", "amf"]:
        if has_encoder(encoders[hw], ffmpeg_path):
            return encoders[hw]

    return "libx264"


def get_best_h265_encoder(ffmpeg_path: str = "ffmpeg", prefer: str = "auto") -> str:
    """
    Get the best available H.265/HEVC encoder.
    Priority: NVENC > QSV > AMF > libx265 (CPU)
    """
    if prefer == "cpu":
        return "libx265"

    encoders = HARDWARE_ENCODERS["h265"]
    if prefer in encoders and prefer != "cpu":
        if has_encoder(encoders[prefer], ffmpeg_path):
            return encoders[prefer]

    for hw in ["nvenc", "qsv", "amf"]:
        if has_encoder(encoders[hw], ffmpeg_path):
            return encoders[hw]

    return "libx265"


def get_gpu_info(ffmpeg_path: str = "ffmpeg") -> dict:
    """
    Return a summary of available GPU encoding support.
    """
    available = detect_available_encoders(ffmpeg_path)
    return {
        "nvidia_nvenc": any(enc in available for enc in ["h264_nvenc", "hevc_nvenc"]),
        "intel_qsv": any(enc in available for enc in ["h264_qsv", "hevc_qsv"]),
        "amd_amf": any(enc in available for enc in ["h264_amf", "hevc_amf"]),
        "best_h264": get_best_h264_encoder(ffmpeg_path),
        "best_h265": get_best_h265_encoder(ffmpeg_path),
        "available_hw_encoders": [
            enc for enc in available
            if any(hw in enc for hw in ["nvenc", "qsv", "amf", "videotoolbox"])
        ],
    }
