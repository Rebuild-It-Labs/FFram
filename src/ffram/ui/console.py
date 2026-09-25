"""Console output, theming, and formatting helpers."""

import sys
import os

if os.name == "nt":
    os.environ.setdefault("PYTHONUTF8", "1")
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich import box
import pyfiglet

THEME = Theme({
    "title": "bold bright_cyan",
    "subtitle": "dim cyan",
    "success": "bold green",
    "error": "bold red",
    "warning": "bold yellow",
    "info": "bold blue",
    "highlight": "bold magenta",
    "dim": "dim white",
    "path": "underline bright_white",
    "command": "bold bright_yellow",
    "category": "bold bright_green",
    "operation": "bright_white",
})

console = Console(theme=THEME)


def print_banner():
    art = pyfiglet.figlet_format("ffram", font="slant")
    console.print(Text(art, style="bold bright_cyan"), justify="center")
    console.print("[subtitle]=== Fast FFmpeg Renderer for Audio and Moving-pictures ===[/subtitle]", justify="center")
    console.print("[dim]102 Operations | 18 Categories | GPU Accelerated[/dim]", justify="center")
    console.print()


def print_media_info(info):
    table = Table(title=f"[FILE] {info.file_path.name}", box=box.ROUNDED,
                  border_style="bright_cyan", title_style="bold bright_white", padding=(0, 1))
    table.add_column("Property", style="bright_cyan", min_width=16)
    table.add_column("Value", style="bright_white", min_width=30)

    table.add_row("Path", str(info.file_path.parent))
    table.add_row("Format", f"{info.format_name} ({info.format_long_name})")
    table.add_row("Duration", info.duration_formatted)
    table.add_row("Size", info.size_formatted)
    table.add_row("Bitrate", f"{info.bitrate // 1000} kbps" if info.bitrate else "N/A")

    if info.has_video:
        vs = info.video_stream
        table.add_row("", "")
        table.add_row("Video Codec", f"{vs.codec_name} ({vs.profile})" if vs.profile else vs.codec_name)
        table.add_row("Resolution", f"{vs.width}x{vs.height} ({info.resolution_label})")
        table.add_row("Frame Rate", f"{vs.fps} fps")
        table.add_row("Pixel Format", vs.pix_fmt)

    if info.has_audio:
        a = info.audio_stream
        table.add_row("", "")
        table.add_row("Audio Codec", a.codec_name)
        table.add_row("Sample Rate", f"{a.sample_rate} Hz")
        table.add_row("Channels", f"{a.channels} ({a.channel_layout})" if a.channel_layout else str(a.channels))
        if a.bitrate:
            table.add_row("Audio Bitrate", f"{a.bitrate // 1000} kbps")

    if info.subtitle_streams:
        table.add_row("", "")
        for idx, sub in enumerate(info.subtitle_streams):
            lang = sub.language or "unknown"
            table.add_row(f"Subtitle {idx + 1}", f"{sub.codec_name} ({lang})")

    console.print(table)
    console.print()


def print_success(msg):
    console.print(f"\n  [success][OK] {msg}[/success]\n")

def print_error(msg):
    console.print(f"\n  [error][ERR] {msg}[/error]\n")

def print_warning(msg):
    console.print(f"\n  [warning][WARN] {msg}[/warning]\n")

def print_info(msg):
    console.print(f"\n  [info]{msg}[/info]\n")

def print_command(cmd):
    import subprocess
    s = subprocess.list2cmdline([str(a) for a in cmd]) if isinstance(cmd, (list, tuple)) else str(cmd)
    console.print(Panel(f"[command]{s}[/command]", title="[dim]FFmpeg Command[/dim]", border_style="dim yellow", padding=(0, 1)))

def print_section(title):
    console.print(f"\n  [category]> {title}[/category]")

def format_elapsed(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    return f"{int(seconds) // 60}m {seconds % 60:.1f}s"
