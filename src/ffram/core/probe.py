"""
core/probe.py - FFprobe wrapper for media file inspection.
Returns structured MediaInfo objects with duration, codecs, resolution, etc.
"""

import subprocess
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class StreamInfo:
    """Information about a single media stream."""
    index: int
    codec_type: str  # "video", "audio", "subtitle", "data"
    codec_name: str
    codec_long_name: str = ""
    profile: str = ""
    # Video-specific
    width: int = 0
    height: int = 0
    fps: float = 0.0
    pix_fmt: str = ""
    # Audio-specific
    sample_rate: int = 0
    channels: int = 0
    channel_layout: str = ""
    # Common
    bitrate: int = 0
    duration: float = 0.0
    language: str = ""
    title: str = ""
    # Color & Dynamic Range
    color_space: str = ""
    color_primaries: str = ""
    color_trc: str = ""
    bits_per_raw_sample: int = 0

    @property
    def bit_depth(self) -> int:
        """Estimate color bit depth (e.g. 8, 10, 12, 16)."""
        if self.bits_per_raw_sample and self.bits_per_raw_sample > 0:
            return self.bits_per_raw_sample
        p = self.pix_fmt.lower()
        if any(k in p for k in ["12le", "12be", "p12"]):
            return 12
        if any(k in p for k in ["10le", "10be", "p10"]):
            return 10
        if any(k in p for k in ["16le", "16be"]):
            return 16
        if any(k in p for k in ["9le", "9be"]):
            return 9
        return 8

    @property
    def is_hdr(self) -> bool:
        """Return True if stream uses HDR transfer characteristics or wide color gamut."""
        trc = str(self.color_trc).lower()
        pri = str(self.color_primaries).lower()
        if any(h in trc for h in ["smpte2084", "arib-std-b67", "hlg", "pq", "16", "18"]):
            return True
        if ("bt2020" in pri or "9" == pri) and self.bit_depth >= 10:
            return True
        return False

    @property
    def hdr_format(self) -> str:
        """User-friendly HDR format label (HDR10, HLG, or SDR)."""
        trc = str(self.color_trc).lower()
        if "smpte2084" in trc or trc == "16" or "pq" in trc:
            return "HDR10"
        if "arib-std-b67" in trc or trc == "18" or "hlg" in trc:
            return "HLG"
        if self.is_hdr:
            return "HDR"
        return "SDR"

    @property
    def audio_summary(self) -> str:
        """User-friendly summary of the audio stream."""
        parts = []
        if self.codec_name and self.codec_name != "unknown":
            parts.append(self.codec_name.upper())
        if self.channel_layout:
            parts.append(self.channel_layout)
        elif self.channels:
            parts.append(f"{self.channels}ch")
        if self.sample_rate:
            parts.append(f"{self.sample_rate}Hz")
        if self.bitrate and self.bitrate > 0:
            parts.append(f"{self.bitrate // 1000}kbps")
        if self.language and self.language != "und":
            parts.append(f"[{self.language}]")
        if self.title:
            parts.append(f'"{self.title}"')
        return " - ".join(parts) if parts else "Audio Track"

    @classmethod
    def from_dict(cls, data: dict) -> "StreamInfo":
        tags = data.get("tags", {})
        fps = 0.0
        r_frame_rate = data.get("r_frame_rate", "0/1")
        if "/" in r_frame_rate:
            num, den = r_frame_rate.split("/")
            if int(den) > 0:
                fps = round(int(num) / int(den), 2)

        title = tags.get("title") or tags.get("name") or tags.get("handler_name", "")
        return cls(
            index=data.get("index", 0),
            codec_type=data.get("codec_type", "unknown"),
            codec_name=data.get("codec_name", "unknown"),
            codec_long_name=data.get("codec_long_name", ""),
            profile=data.get("profile", ""),
            width=int(data.get("width", 0)),
            height=int(data.get("height", 0)),
            fps=fps,
            pix_fmt=data.get("pix_fmt", ""),
            sample_rate=int(data.get("sample_rate", 0)),
            channels=int(data.get("channels", 0)),
            channel_layout=data.get("channel_layout", ""),
            bitrate=int(data.get("bit_rate", 0)),
            duration=float(data.get("duration", 0)),
            language=tags.get("language", ""),
            title=title,
            color_space=str(data.get("color_space") or ""),
            color_primaries=str(data.get("color_primaries") or ""),
            color_trc=str(data.get("color_transfer") or data.get("color_trc") or ""),
            bits_per_raw_sample=int(data.get("bits_per_raw_sample") or data.get("bits_per_sample") or 0),
        )


@dataclass
class MediaInfo:
    """Complete media file information from ffprobe."""
    file_path: Path
    format_name: str = ""
    format_long_name: str = ""
    duration: float = 0.0
    size: int = 0
    bitrate: int = 0
    nb_streams: int = 0
    streams: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    # Convenience accessors
    @property
    def video_stream(self) -> Optional[StreamInfo]:
        for s in self.streams:
            if s.codec_type == "video":
                return s
        return None

    @property
    def video_streams(self) -> list:
        return [s for s in self.streams if s.codec_type == "video"]

    @property
    def audio_stream(self) -> Optional[StreamInfo]:
        for s in self.streams:
            if s.codec_type == "audio":
                return s
        return None

    @property
    def audio_streams(self) -> list:
        return [s for s in self.streams if s.codec_type == "audio"]

    @property
    def subtitle_streams(self) -> list:
        return [s for s in self.streams if s.codec_type == "subtitle"]

    @property
    def has_video(self) -> bool:
        return self.video_stream is not None

    @property
    def has_audio(self) -> bool:
        return self.audio_stream is not None

    @property
    def width(self) -> int:
        vs = self.video_stream
        return vs.width if vs else 0

    @property
    def height(self) -> int:
        vs = self.video_stream
        return vs.height if vs else 0

    @property
    def fps(self) -> float:
        vs = self.video_stream
        return vs.fps if vs else 0.0

    @property
    def video_codec(self) -> str:
        vs = self.video_stream
        return vs.codec_name if vs else ""

    @property
    def audio_codec(self) -> str:
        aus = self.audio_stream
        return aus.codec_name if aus else ""

    @property
    def resolution_label(self) -> str:
        vs = self.video_stream
        if not vs:
            return "Audio Only" if self.has_audio else "N/A"
        w, h = vs.width, vs.height
        if w >= 7600 or h >= 4300:
            return "8K UHD"
        elif w >= 3800 or h >= 2100:
            return "4K UHD"
        elif w >= 2500 or h >= 1000 and (w >= 2400 or h >= 1400):
            return "1440p (2K)"
        elif w >= 1900 or h >= 1000 or (w >= 1800 and h >= 750):
            return "1080p (Full HD)"
        elif w >= 1200 or h >= 700 or (w >= 1100 and h >= 500):
            return "720p (HD)"
        elif w >= 700 or h >= 480:
            return "480p (SD)"
        elif w >= 480 or h >= 360:
            return "360p"
        elif h > 0:
            return f"{h}p"
        return "Unknown"

    @property
    def quality_badge(self) -> str:
        """Concise one-line summary of file media quality."""
        if not self.has_video and self.has_audio:
            aus = self.audio_stream
            return f"Audio ({aus.codec_name.upper()} {aus.sample_rate}Hz)"
        vs = self.video_stream
        if not vs:
            return "Unknown"
        parts = [self.resolution_label]
        if vs.is_hdr:
            parts.append(vs.hdr_format)
        elif vs.bit_depth > 8:
            parts.append(f"{vs.bit_depth}-bit")
        return " ".join(parts)

    @property
    def duration_formatted(self) -> str:
        total = int(self.duration)
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

    @property
    def size_formatted(self) -> str:
        if self.size >= 1_073_741_824:
            return f"{self.size / 1_073_741_824:.2f} GB"
        elif self.size >= 1_048_576:
            return f"{self.size / 1_048_576:.1f} MB"
        elif self.size >= 1024:
            return f"{self.size / 1024:.1f} KB"
        return f"{self.size} B"


def probe(file_path: str | Path, ffprobe_path: str = "ffprobe") -> MediaInfo:
    """
    Run probe on a media file and return structured MediaInfo.
    Uses PyAV for instant metadata extraction, with a fallback to ffprobe.
    """
    import os
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        import av
        with av.open(str(file_path)) as container:
            streams = []
            for s in container.streams:
                duration = float(s.duration * s.time_base) if s.duration and s.time_base else 0.0
                ctx = s.codec_context
                if s.type == "video":
                    fps = float(s.average_rate) if s.average_rate else 0.0
                    v_bitrate = ctx.bit_rate if ctx and ctx.bit_rate else 0
                    if not v_bitrate and "BPS" in s.metadata:
                        try:
                            v_bitrate = int(s.metadata["BPS"])
                        except ValueError:
                            pass
                    profile_name = getattr(ctx, "profile", "") or ""
                    streams.append(StreamInfo(
                        index=s.index,
                        codec_type="video",
                        codec_name=ctx.name if ctx else "",
                        codec_long_name=ctx.long_name if ctx else "",
                        profile=str(profile_name),
                        width=ctx.width if ctx else 0,
                        height=ctx.height if ctx else 0,
                        fps=fps,
                        pix_fmt=ctx.pix_fmt if ctx else "",
                        bitrate=v_bitrate,
                        duration=duration,
                        language=s.metadata.get("language", ""),
                        title=s.metadata.get("title", ""),
                        color_space=str(getattr(ctx, "colorspace", "") or ""),
                        color_primaries=str(getattr(ctx, "color_primaries", "") or ""),
                        color_trc=str(getattr(ctx, "color_trc", "") or ""),
                        bits_per_raw_sample=int(getattr(ctx, "bits_per_raw_sample", 0) or 0),
                    ))
                elif s.type == "audio":
                    layout_name = ""
                    if hasattr(ctx, "layout") and ctx.layout:
                        layout_name = getattr(ctx.layout, "name", "")
                    title = s.metadata.get("title") or s.metadata.get("name", "")
                    a_bitrate = ctx.bit_rate if ctx and ctx.bit_rate else 0
                    if not a_bitrate and "BPS" in s.metadata:
                        try:
                            a_bitrate = int(s.metadata["BPS"])
                        except ValueError:
                            pass
                    streams.append(StreamInfo(
                        index=s.index,
                        codec_type="audio",
                        codec_name=ctx.name if ctx else "",
                        codec_long_name=ctx.long_name if ctx else "",
                        sample_rate=ctx.sample_rate if ctx else 0,
                        channels=ctx.channels if ctx else 0,
                        channel_layout=layout_name,
                        bitrate=a_bitrate,
                        duration=duration,
                        language=s.metadata.get("language", ""),
                        title=title
                    ))
                elif s.type == "subtitle":
                    streams.append(StreamInfo(
                        index=s.index,
                        codec_type="subtitle",
                        codec_name=ctx.name if ctx else "",
                        duration=duration,
                        language=s.metadata.get("language", ""),
                        title=s.metadata.get("title", "")
                    ))
                else:
                    streams.append(StreamInfo(
                        index=s.index,
                        codec_type="data",
                        codec_name=ctx.name if ctx else "",
                        duration=duration,
                    ))

            container_duration = float(container.duration / av.time_base) if container.duration else 0.0
            size = os.path.getsize(file_path)
            bitrate = container.bit_rate or 0
            
            return MediaInfo(
                file_path=file_path,
                format_name=container.format.name,
                format_long_name=container.format.long_name,
                duration=container_duration,
                size=size,
                bitrate=bitrate,
                nb_streams=len(streams),
                streams=streams,
                metadata=container.metadata,
            )
    except Exception as e:
        # Fallback to ffprobe if PyAV is not installed or fails for this format
        pass

    # --- FFprobe fallback ---
    cmd = [
        ffprobe_path,
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe not found. Ensure FFmpeg is installed and in your PATH."
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"ffprobe timed out while probing: {file_path}")

    stdout_str = result.stdout.decode("utf-8", errors="replace")
    stderr_str = result.stderr.decode("utf-8", errors="replace")

    if result.returncode != 0:
        raise RuntimeError(f"ffprobe error: {stderr_str.strip()}")

    data = json.loads(stdout_str)
    fmt = data.get("format", {})
    tags = fmt.get("tags", {})

    streams = []
    for stream_data in data.get("streams", []):
        streams.append(StreamInfo.from_dict(stream_data))

    return MediaInfo(
        file_path=file_path,
        format_name=fmt.get("format_name", ""),
        format_long_name=fmt.get("format_long_name", ""),
        duration=float(fmt.get("duration", 0)),
        size=int(fmt.get("size", 0)),
        bitrate=int(fmt.get("bit_rate", 0)),
        nb_streams=int(fmt.get("nb_streams", 0)),
        streams=streams,
        metadata=tags,
    )


def get_duration(file_path: str | Path, ffprobe_path: str = "ffprobe") -> float:
    """Quick helper to get just the duration in seconds."""
    info = probe(file_path, ffprobe_path)
    return info.duration
