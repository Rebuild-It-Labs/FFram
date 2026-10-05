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
    "title": "bold #8be9fd",
    "subtitle": "dim #6272a4",
    "success": "bold #50fa7b",
    "error": "bold #ff5555",
    "warning": "bold #f1fa8c",
    "info": "bold #8be9fd",
    "highlight": "bold #bd93f9",
    "dim": "dim #f8f8f2",
    "path": "underline #f1fa8c",
    "command": "bold #ffb86c",
    "category": "bold #50fa7b",
    "operation": "#f8f8f2",
})

console = Console(theme=THEME)


def print_banner():
    art = pyfiglet.figlet_format("ffram", font="slant")
    console.print(Text(art, style="bold #8be9fd"), justify="center")
    console.print("[subtitle]=== Fast FFmpeg Renderer for Audio and Moving-pictures ===[/subtitle]", justify="center")
    console.print()


def print_media_info(info):
    import datetime
    
    try:
        stat = info.file_path.stat()
        mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        mtime = "Unknown"
        
    table = Table(title=f"[FILE] {info.file_path.name}", box=box.ROUNDED,
                  border_style="#6272a4", title_style="bold #f8f8f2", padding=(0, 1))
    table.add_column("Property", style="#8be9fd", min_width=16)
    table.add_column("Value", style="#f8f8f2", min_width=30)

    table.add_row("Path", str(info.file_path.parent))
    table.add_row("Extension", info.file_path.suffix)
    table.add_row("Modified", mtime)
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

def print_parameter_summary(op_name: str, params: dict):
    if not params:
        return
    table = Table(title=f"Parameters for {op_name}", box=box.SIMPLE, border_style="#6272a4")
    table.add_column("Parameter", style="#bd93f9")
    table.add_column("Value", style="#f8f8f2")
    for k, v in params.items():
        if k not in ["input_path", "second_input_path", "duration", "file_list", "workers"]:
            table.add_row(str(k), str(v))
    if table.row_count > 0:
        console.print(table)
        console.print()

def print_io_comparison(input_info, output_info):
    table = Table(title="Input vs Output Comparison", box=box.ROUNDED, border_style="#50fa7b")
    table.add_column("Property", style="#8be9fd")
    table.add_column("Original Input", style="#f1fa8c")
    table.add_column("Generated Output", style="#50fa7b")
    
    table.add_row("Name", input_info.file_path.name, output_info.file_path.name)
    table.add_row("Size", input_info.size_formatted, output_info.size_formatted)
    table.add_row("Duration", input_info.duration_formatted, output_info.duration_formatted)
    table.add_row("Resolution", input_info.resolution_label, output_info.resolution_label)
    
    in_v_codec = input_info.video_codec if input_info.has_video else "N/A"
    out_v_codec = output_info.video_codec if output_info.has_video else "N/A"
    table.add_row("Video Codec", in_v_codec, out_v_codec)
    
    in_a_codec = input_info.audio_codec if input_info.has_audio else "N/A"
    out_a_codec = output_info.audio_codec if output_info.has_audio else "N/A"
    table.add_row("Audio Codec", in_a_codec, out_a_codec)
    
    console.print(table)
    console.print()

def print_quick_stats(elapsed_time, gpu_accel=False):
    accel = "[#50fa7b]Enabled[/#50fa7b]" if gpu_accel else "[dim]None[/dim]"
    console.print(Panel(
        f"⏱️ Time: [#f1fa8c]{format_elapsed(elapsed_time)}[/#f1fa8c] | 🚀 HW Accel: {accel}",
        style="dim", box=box.ROUNDED
    ))
