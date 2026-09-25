"""
ui/console.py - Rich console styling, banners, headers, and formatted output.
"""

import sys
import os

# Force UTF-8 on Windows before importing Rich
if os.name == "nt":
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich import box
import pyfiglet

# Custom theme for the toolkit
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
    """Print banner."""
    ascii_art = pyfiglet.figlet_format("ffram", font="slant")
    banner_text = Text(ascii_art, style="bold bright_cyan")

    console.print(banner_text, justify="center")
    console.print(
        "[subtitle]=== Fast FFmpeg Renderer for Audio and Moving-pictures ===[/subtitle]",
        justify="center",
    )
    console.print(
        "[dim]102 Media Processing Operations | 18 Specialized Categories | GPU Accelerated[/dim]",
        justify="center",
    )
    console.print()


def print_media_info(info):
    """Print media info."""
    table = Table(
        title=f"[FILE] {info.file_path.name}",
        box=box.ROUNDED,
        border_style="bright_cyan",
        title_style="bold bright_white",
        padding=(0, 1),
    )

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
        aus = info.audio_stream
        table.add_row("", "")
        table.add_row("Audio Codec", aus.codec_name)
        table.add_row("Sample Rate", f"{aus.sample_rate} Hz")
        table.add_row("Channels", f"{aus.channels} ({aus.channel_layout})" if aus.channel_layout else str(aus.channels))
        if aus.bitrate:
            table.add_row("Audio Bitrate", f"{aus.bitrate // 1000} kbps")

    if info.subtitle_streams:
        table.add_row("", "")
        for i, sub in enumerate(info.subtitle_streams):
            lang = sub.language if sub.language else "unknown"
            table.add_row(f"Subtitle {i + 1}", f"{sub.codec_name} ({lang})")

    console.print(table)
    console.print()


def print_success(message: str):
    console.print(f"\n  [success][OK] {message}[/success]\n")


def print_error(message: str):
    console.print(f"\n  [error][ERR] {message}[/error]\n")


def print_warning(message: str):
    console.print(f"\n  [warning][WARN] {message}[/warning]\n")


def print_info(message: str):
    console.print(f"\n  [info][i] {message}[/info]\n")


def print_command(cmd):
    """Print the FFmpeg command being executed, automatically quoting paths with spaces."""
    import subprocess
    if isinstance(cmd, (list, tuple)):
        cmd_str = subprocess.list2cmdline([str(arg) for arg in cmd])
    else:
        cmd_str = str(cmd)
    console.print(
        Panel(
            f"[command]{cmd_str}[/command]",
            title="[dim]FFmpeg Command[/dim]",
            border_style="dim yellow",
            padding=(0, 1),
        )
    )


def print_section(title: str):
    """Print a section header."""
    console.print(f"\n  [category]> {title}[/category]")


def format_elapsed(seconds: float) -> str:
    """Format elapsed time for display."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    m = int(seconds) // 60
    s = seconds % 60
    return f"{m}m {s:.1f}s"
