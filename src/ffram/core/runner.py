"""
core/runner.py - FFmpeg subprocess execution with real-time progress parsing.
Handles running FFmpeg commands, parsing progress output, and providing
callbacks for live progress display.
"""

import subprocess
import re
import time
import signal
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ProgressInfo:
    """Real-time progress data parsed from FFmpeg output."""
    frame: int = 0
    fps: float = 0.0
    total_size: int = 0
    out_time_seconds: float = 0.0
    bitrate: str = ""
    speed: str = ""
    percent: float = 0.0
    eta_seconds: float = 0.0


@dataclass
class RunResult:
    """Result of an FFmpeg command execution."""
    success: bool
    return_code: int
    output_file: Optional[Path] = None
    elapsed_seconds: float = 0.0
    error_message: str = ""
    command: str = ""


def _parse_time_to_seconds(time_str: str) -> float:
    """Convert HH:MM:SS.xx or similar time string to seconds."""
    time_str = time_str.strip()
    # Handle microsecond format from -progress output
    if time_str.replace(".", "").replace("-", "").isdigit() and len(time_str) > 10:
        try:
            return float(time_str) / 1_000_000.0
        except ValueError:
            pass

    # Handle HH:MM:SS.xx format
    match = re.match(r"(-?)(\d+):(\d+):(\d+(?:\.\d+)?)", time_str)
    if match:
        sign = -1 if match.group(1) == "-" else 1
        h = int(match.group(2))
        m = int(match.group(3))
        s = float(match.group(4))
        return sign * (h * 3600 + m * 60 + s)
    return 0.0


def run_ffmpeg(
    cmd: list[str],
    duration: float = 0.0,
    on_progress: Optional[Callable[[ProgressInfo], None]] = None,
    ffmpeg_path: str = "ffmpeg",
) -> RunResult:
    """
    Execute an FFmpeg command with real-time progress tracking.

    Args:
        cmd: FFmpeg command arguments (without the 'ffmpeg' binary itself).
        duration: Total expected duration in seconds (for percentage calculation).
        on_progress: Callback function invoked with ProgressInfo updates.
        ffmpeg_path: Path to ffmpeg executable.

    Returns:
        RunResult with success status, timing, and error details.
    """
    full_cmd = [ffmpeg_path] + cmd

    # Add -y to overwrite without asking (we handle confirmation in the UI layer)
    if "-y" not in full_cmd:
        full_cmd.insert(1, "-y")

    # Add progress output to stderr for parsing
    command_str = " ".join(f'"{c}"' if " " in c else c for c in full_cmd)

    start_time = time.time()

    try:
        process = subprocess.Popen(
            full_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            universal_newlines=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
    except FileNotFoundError:
        return RunResult(
            success=False,
            return_code=-1,
            error_message="FFmpeg not found. Ensure FFmpeg is installed and in your PATH.",
            command=command_str,
        )

    stderr_data = b""
    progress = ProgressInfo()

    try:
        # Read stderr in real-time for progress parsing
        while True:
            chunk = process.stderr.read(1024)
            if not chunk:
                break
            stderr_data += chunk
            text = chunk.decode("utf-8", errors="replace")

            # Parse time= from stderr
            time_matches = re.findall(r"time=(\S+)", text)
            if time_matches:
                current_time = _parse_time_to_seconds(time_matches[-1])
                if current_time > 0:
                    progress.out_time_seconds = current_time
                    if duration > 0:
                        progress.percent = min(
                            (current_time / duration) * 100, 100.0
                        )
                        elapsed = time.time() - start_time
                        if progress.percent > 0:
                            total_est = elapsed / (progress.percent / 100.0)
                            progress.eta_seconds = max(0, total_est - elapsed)

            # Parse fps=
            fps_matches = re.findall(r"fps=\s*(\d+(?:\.\d+)?)", text)
            if fps_matches:
                progress.fps = float(fps_matches[-1])

            # Parse speed=
            speed_matches = re.findall(r"speed=\s*(\S+)", text)
            if speed_matches:
                progress.speed = speed_matches[-1]

            # Parse frame=
            frame_matches = re.findall(r"frame=\s*(\d+)", text)
            if frame_matches:
                progress.frame = int(frame_matches[-1])

            # Parse bitrate=
            bitrate_matches = re.findall(r"bitrate=\s*(\S+)", text)
            if bitrate_matches:
                progress.bitrate = bitrate_matches[-1]

            # Parse size=
            size_matches = re.findall(r"size=\s*(\d+)", text)
            if size_matches:
                progress.total_size = int(size_matches[-1])

            if on_progress and progress.out_time_seconds > 0:
                on_progress(progress)

        process.wait()

    except KeyboardInterrupt:
        process.terminate()
        process.wait()
        return RunResult(
            success=False,
            return_code=-2,
            elapsed_seconds=time.time() - start_time,
            error_message="Operation cancelled by user.",
            command=command_str,
        )

    elapsed = time.time() - start_time

    if process.returncode == 0:
        # Final 100% progress callback
        if on_progress and duration > 0:
            progress.percent = 100.0
            progress.eta_seconds = 0
            on_progress(progress)

        return RunResult(
            success=True,
            return_code=0,
            elapsed_seconds=elapsed,
            command=command_str,
        )
    else:
        stderr_text = stderr_data.decode("utf-8", errors="replace")
        # Extract the most meaningful error line
        error_lines = [
            line for line in stderr_text.splitlines()
            if any(kw in line.lower() for kw in ["error", "invalid", "no such", "not found", "failed"])
        ]
        error_msg = error_lines[-1] if error_lines else stderr_text[-500:]

        return RunResult(
            success=False,
            return_code=process.returncode,
            elapsed_seconds=elapsed,
            error_message=error_msg.strip(),
            command=command_str,
        )


def run_ffmpeg_simple(cmd: list[str], ffmpeg_path: str = "ffmpeg") -> RunResult:
    """Run FFmpeg without progress tracking. For quick operations."""
    return run_ffmpeg(cmd, duration=0, on_progress=None, ffmpeg_path=ffmpeg_path)


def run_two_pass(
    pass1_cmd: list[str],
    pass2_cmd: list[str],
    duration: float = 0.0,
    on_progress: Optional[Callable[[ProgressInfo], None]] = None,
    ffmpeg_path: str = "ffmpeg",
) -> RunResult:
    """
    Execute a 2-pass FFmpeg encoding.
    Pass 1 runs analysis (typically outputs to NUL), Pass 2 produces the final file.
    Progress is reported across both passes (0-50% for pass 1, 50-100% for pass 2).
    """
    def pass1_progress(info: ProgressInfo):
        if on_progress:
            info.percent = info.percent / 2  # 0-50%
            on_progress(info)

    def pass2_progress(info: ProgressInfo):
        if on_progress:
            info.percent = 50 + info.percent / 2  # 50-100%
            on_progress(info)

    result1 = run_ffmpeg(pass1_cmd, duration, pass1_progress, ffmpeg_path)
    if not result1.success:
        return result1

    result2 = run_ffmpeg(pass2_cmd, duration, pass2_progress, ffmpeg_path)
    result2.elapsed_seconds += result1.elapsed_seconds
    return result2
