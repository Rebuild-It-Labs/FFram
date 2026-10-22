"""Interactive menu system for ffram."""

from pathlib import Path
from typing import Optional
import json
import time
import datetime
from InquirerPy import inquirer
from InquirerPy.separator import Separator
from rich.table import Table
from rich import box

from ffram.categories.base import OperationInfo
from ffram.categories.audio_extract import AudioExtractOps
from ffram.categories.audio_manage import AudioManageOps
from ffram.categories.convert import ConvertOps
from ffram.categories.compress import CompressOps
from ffram.categories.resize import ResizeOps
from ffram.categories.cut_trim import CutTrimOps
from ffram.categories.track_clean import TrackCleanOps
from ffram.categories.audio_filter import AudioFilterOps
from ffram.categories.video_fx import VideoFXOps
from ffram.categories.speed import SpeedOps
from ffram.categories.screenshot_gif import ScreenshotGifOps
from ffram.categories.concat import ConcatOps
from ffram.categories.watermark import WatermarkOps
from ffram.categories.crop_pad import CropPadOps
from ffram.categories.subtitles import SubtitleOps
from ffram.categories.metadata import MetadataOps
from ffram.categories.batch import BatchOps
from ffram.categories.combos import ComboOps

from ffram.core.validator import validate_input_file
from ffram.core.probe import probe
from ffram.ui.dialogs import pick_file, pick_files, pick_directory, MEDIA_FILTERS, VIDEO_FILTERS, AUDIO_FILTERS, IMAGE_FILTERS, SUBTITLE_FILTERS
from ffram.ui.console import console, print_success, print_error, print_warning, print_section, print_parameter_summary, print_io_comparison, print_quick_stats

RECENT_FILES_CACHE = Path.home() / ".ffram_recent.json"

def load_recent_files():
    if not RECENT_FILES_CACHE.exists():
        return []
    try:
        with open(RECENT_FILES_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_recent_file(path_str: str, op_name: str):
    recent = load_recent_files()
    entry = {"path": path_str, "op": op_name, "date": datetime.datetime.now().isoformat()}
    recent = [r for r in recent if r["path"] != path_str]
    recent.insert(0, entry)
    recent = recent[:10]  # Keep last 10
    try:
        with open(RECENT_FILES_CACHE, "w", encoding="utf-8") as f:
            json.dump(recent, f, indent=4)
    except Exception:
        pass

def generate_report(input_info, output_info, params, op_name, elapsed_time):
    report_path = output_info.file_path.with_suffix(".report.md")
    lines = [
        f"# FFram Operation Report: {op_name}",
        f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Time Elapsed:** {elapsed_time:.2f} seconds",
        "",
        "## Parameters",
    ]
    for k, v in params.items():
        if k not in ["input_path", "second_input_path", "duration", "file_list", "workers"]:
            lines.append(f"- **{k}**: {v}")
    
    lines.extend([
        "",
        "## Input vs Output Comparison",
        "| Property | Original Input | Generated Output |",
        "|---|---|---|",
        f"| Name | {input_info.file_path.name} | {output_info.file_path.name} |",
        f"| Size | {input_info.size_formatted} | {output_info.size_formatted} |",
        f"| Duration | {input_info.duration_formatted} | {output_info.duration_formatted} |",
        f"| Resolution | {input_info.resolution_label} | {output_info.resolution_label} |",
        f"| Video Codec | {input_info.video_codec if input_info.has_video else 'N/A'} | {output_info.video_codec if output_info.has_video else 'N/A'} |",
        f"| Audio Codec | {input_info.audio_codec if input_info.has_audio else 'N/A'} | {output_info.audio_codec if output_info.has_audio else 'N/A'} |",
    ])
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        console.print(f"  [dim]-> Report saved: {report_path}[/dim]")
    except Exception as e:
        print_warning(f"Could not save report: {e}")

OPERATION_MODULES = [
    AudioExtractOps(), AudioManageOps(), ConvertOps(), CompressOps(),
    ResizeOps(), CutTrimOps(), TrackCleanOps(), AudioFilterOps(),
    VideoFXOps(), SpeedOps(), ScreenshotGifOps(), ConcatOps(),
    WatermarkOps(), CropPadOps(), SubtitleOps(), MetadataOps(),
    BatchOps(), ComboOps(),
]

# (display_label, internal_category_name)
CATEGORIES = [
    ("[1]  Video > Audio", "Video > Audio"),
    ("[2]  Audio Management", "Audio Management"),
    ("[3]  Video Conversion", "Video Conversion"),
    ("[4]  Compress Video", "Compress Video"),
    ("[5]  Resize Video", "Resize Video"),
    ("[6]  Cut / Trim", "Cut / Trim"),
    ("[7]  Remove Tracks", "Remove Tracks"),
    ("[8]  Audio Processing", "Audio Processing"),
    ("[9]  Video Effects", "Video Effects"),
    ("[10] Video Speed", "Video Speed"),
    ("[11] Screenshots / GIF", "Screenshots / GIF"),
    ("[12] Combine Videos", "Combine Videos"),
    ("[13] Overlay / Watermark", "Overlay / Watermark"),
    ("[14] Crop / Aspect Ratio", "Crop / Aspect Ratio"),
    ("[15] Subtitles", "Subtitles"),
    ("[16] Metadata", "Metadata"),
    ("[17] Batch Processing", "Batch Processing"),
    ("[18] Smart Combos", "Smart Combos"),
]


def get_all_operations():
    ops = []
    for mod in OPERATION_MODULES:
        for op in mod.get_operations():
            ops.append((op, mod))
    return ops


def prompt_file_input(prompt_text="Input file", file_types=None, allow_browse=True):
    while True:
        user_input = inquirer.text(
            message=f"{prompt_text} [Enter=Browse, or paste path]:",
            default="", validate=lambda _: True,
        ).execute()

        if not user_input or user_input.strip().lower() in ("b", "browse"):
            if allow_browse:
                console.print("  [dim]Opening file picker...[/dim]")
                selected = pick_file(title=prompt_text, file_types=file_types or MEDIA_FILTERS)
                if selected:
                    console.print(f"  [path]Selected: {selected}[/path]")
                    return selected
                print_warning("No file selected. Try again or type 'q' to cancel.")
                continue
            print_warning("Please enter a file path.")
            continue

        if user_input.strip().lower() in ("q", "quit", "cancel"):
            return None

        valid, err, resolved = validate_input_file(user_input)
        if valid:
            return resolved
        print_error(err)


def prompt_multi_file_input(prompt_text="Select files", file_types=None):
    console.print(f"  [dim]{prompt_text} - Opening file picker...[/dim]")
    files = pick_files(title=prompt_text, file_types=file_types or VIDEO_FILTERS)
    if files:
        console.print(f"  [path]Selected {len(files)} files[/path]")
    return files


def prompt_directory_input(prompt_text="Select folder"):
    user_input = inquirer.text(message=f"{prompt_text} [Enter=Browse]:", default="").execute()
    if not user_input or user_input.strip().lower() in ("b", "browse"):
        console.print("  [dim]Opening folder picker...[/dim]")
        selected = pick_directory(title=prompt_text)
        if selected:
            console.print(f"  [path]Selected: {selected}[/path]")
            return selected
        return None
    path = Path(user_input.strip().strip('"').strip("'"))
    if path.is_dir():
        return path
    print_error(f"Not a valid directory: {path}")
    return None


def prompt_operation_params(op_info, params):
    cat = op_info.category

    if cat == "Cut / Trim":
        if op_info.id == 38:
            params["cut_duration"] = inquirer.text(message="Duration (seconds):", default="30").execute()
        elif op_info.id == 39:
            params["start_time"] = inquirer.text(message="Start timestamp (HH:MM:SS):", default="00:01:00").execute()
        elif op_info.id == 40:
            params["start_time"] = inquirer.text(message="Start timestamp:", default="00:01:00").execute()
            params["end_time"] = inquirer.text(message="End timestamp:", default="00:02:30").execute()
        elif op_info.id in (41, 42):
            params["start_time"] = inquirer.text(message="Start timestamp:", default="00:01:00").execute()
            params["cut_duration"] = inquirer.text(message="Duration (seconds):", default="30").execute()

    elif op_info.id == 201:
        workers_str = inquirer.text(message="Worker URLs (comma separated):", default="http://localhost:8000").execute()
        params["workers"] = [w.strip() for w in workers_str.split(",") if w.strip()]

    elif op_info.id == 68:
        params["timestamp"] = inquirer.text(message="Screenshot timestamp (HH:MM:SS):", default="00:00:10").execute()

    elif op_info.id == 79:
        params["text"] = inquirer.text(message="Text to overlay:", default="My Video").execute()
        params["font_size"] = inquirer.text(message="Font size:", default="40").execute()
        params["font_color"] = inquirer.select(
            message="Font color:", choices=["white", "yellow", "red", "green", "blue", "black"], default="white",
        ).execute()

    elif op_info.id == 100:
        size = inquirer.select(
            message="Target file size:",
            choices=[
                {"name": "10 MB (Discord free)", "value": 10},
                {"name": "16 MB (WhatsApp)", "value": 16},
                {"name": "25 MB (Discord Nitro Basic)", "value": 25},
                {"name": "50 MB (Discord Nitro)", "value": 50},
                {"name": "100 MB (Large)", "value": 100},
                {"name": "Custom size", "value": 0},
            ],
            default=25,
        ).execute()
        if size == 0:
            size = int(inquirer.text(message="Custom size in MB:", default="25").execute())
        params["target_size_mb"] = size

    elif op_info.id == 101:
        params["gif_fps"] = int(inquirer.text(message="GIF frame rate (fps):", default="15").execute())
        params["gif_width"] = int(inquirer.text(message="GIF width (pixels):", default="640").execute())

    elif op_info.id == 102:
        if inquirer.confirm(message="Trim video?", default=False).execute():
            params["trim_start"] = inquirer.text(message="Trim start:", default="00:00:00").execute()
            params["trim_end"] = inquirer.text(message="Trim end:", default="").execute()
        if inquirer.confirm(message="Resize video?", default=True).execute():
            params["resize_height"] = inquirer.select(
                message="Target resolution:",
                choices=[{"name": "1080p", "value": "1080"}, {"name": "720p", "value": "720"}, {"name": "480p", "value": "480"}],
                default="720",
            ).execute()
        if inquirer.confirm(message="Add text watermark?", default=False).execute():
            params["watermark_text"] = inquirer.text(message="Watermark text:", default="").execute()
        params["normalize_audio"] = inquirer.confirm(message="Normalize audio (EBU R128)?", default=True).execute()
        params["crf"] = inquirer.select(
            message="Compression quality:",
            choices=[{"name": "High (CRF 20)", "value": "20"}, {"name": "Balanced (CRF 23)", "value": "23"}, {"name": "Small (CRF 28)", "value": "28"}],
            default="23",
        ).execute()

    elif op_info.id == 92:
        params["title"] = inquirer.text(message="Video title:", default="My Video").execute()
    elif op_info.id == 93:
        params["artist"] = inquirer.text(message="Artist name:", default="").execute()

    elif cat == "Video Speed":
        if inquirer.confirm(message="Use custom speed factor?", default=False).execute():
            params["speed_factor"] = float(inquirer.text(message="Speed factor:", default="2.0").execute())

    elif op_info.id == 103:
        target_path = Path(params["input_path"])
        source_path = Path(params["second_input_path"])

        try:
            source_info = probe(source_path)
            target_info = probe(target_path)
        except Exception as e:
            print_error(f"Error inspecting files: {e}")
            return params

        source_tracks = source_info.audio_streams
        if not source_tracks:
            print_warning(f"No audio tracks found in source file: {source_path.name}")
            return params

        target_tracks = target_info.audio_streams

        console.print(f"\n  [cyan bold]Target Video (Receives audio):[/cyan bold] [path]{target_path.name}[/path]")
        console.print(f"  [dim]{target_info.resolution_label} | {target_info.video_codec} | {len(target_tracks)} audio track(s) currently[/dim]")

        console.print(f"\n  [cyan bold]Source Video (Audio donor):[/cyan bold] [path]{source_path.name}[/path]")
        console.print(f"  [dim]{len(source_tracks)} audio track(s) detected[/dim]\n")

        # Confirm or Swap roles
        if inquirer.confirm(message="Swap roles? (Current Target will receive audio from Source)", default=False).execute():
            target_path, source_path = source_path, target_path
            target_info, source_info = source_info, target_info
            target_tracks, source_tracks = source_tracks, target_tracks
            params["input_path"] = str(target_path)
            params["second_input_path"] = str(source_path)
            console.print(f"  [green]Roles swapped:[/green] Target is now [path]{target_path.name}[/path]\n")

        # 1. Select track from source video
        if len(source_tracks) == 1:
            console.print(f"  [green]Auto-selected sole audio track:[/green] {source_tracks[0].audio_summary}")
            selected_idx = 0
        else:
            track_choices = [
                {"name": f"Track #{i+1}: {track.audio_summary}", "value": i}
                for i, track in enumerate(source_tracks)
            ]
            selected_idx = inquirer.select(
                message="Select audio track to extract from source video:",
                choices=track_choices,
                default=0,
            ).execute()

        params["source_audio_index"] = selected_idx
        selected_track = source_tracks[selected_idx]

        # 2. Select placement in target video
        placement_choices = [
            {
                "name": f"1. Keep existing audio & APPEND as secondary track (Target will have {len(target_tracks) + 1} tracks)",
                "value": "add_secondary"
            },
            {
                "name": "2. Set as PRIMARY audio track & DEFAULT (Keep existing audio after it)",
                "value": "make_primary"
            },
            {
                "name": "3. ONLY new audio (Replace/remove all existing audio from Target video)",
                "value": "only_new"
            },
        ]

        if len(target_tracks) >= 2:
            placement_choices.append({
                "name": f"4. Replace a specific audio track in Target video (choose 1 of {len(target_tracks)})",
                "value": "replace_specific"
            })

        default_placement = "add_secondary" if target_tracks else "only_new"
        placement_mode = inquirer.select(
            message="How should this audio track be placed in the target video?",
            choices=placement_choices,
            default=default_placement,
        ).execute()
        params["placement_mode"] = placement_mode

        if placement_mode == "replace_specific":
            rep_choices = [
                {"name": f"Track #{i+1}: {track.audio_summary}", "value": i}
                for i, track in enumerate(target_tracks)
            ]
            params["target_replace_index"] = inquirer.select(
                message="Select which existing track in Target video to replace:",
                choices=rep_choices,
                default=0,
            ).execute()

        # 3. Duration handling
        duration_choice = inquirer.select(
            message="Duration handling:",
            choices=[
                {"name": f"Match Target Video duration ({target_info.duration_formatted}) [Recommended]", "value": "video"},
                {"name": "Cut to shortest stream (-shortest)", "value": "shortest"},
            ],
            default="video",
        ).execute()
        params["duration_mode"] = duration_choice

        # 4. Subtitles
        if target_info.subtitle_streams:
            params["include_subtitles"] = inquirer.confirm(
                message=f"Keep subtitles from Target video ({len(target_info.subtitle_streams)} track(s))?",
                default=True,
            ).execute()

        # 5. Optional metadata customization
        if inquirer.confirm(message="Customize track language/title for the new audio?", default=False).execute():
            default_lang = selected_track.language if selected_track.language and selected_track.language != "und" else "eng"
            params["new_track_lang"] = inquirer.text(message="Track language code (e.g. eng, spa, fra, jpn):", default=default_lang).execute()
            params["new_track_title"] = inquirer.text(message="Track title/description:", default=selected_track.title or "").execute()

    elif op_info.id == 104:
        top_path = Path(params["input_path"])
        bot_path = Path(params["second_input_path"])

        try:
            top_info = probe(top_path)
            bot_info = probe(bot_path)
        except Exception as e:
            print_error(f"Error inspecting comparison videos: {e}")
            return params

        console.print(f"\n  [cyan bold]Top Video (Reference):[/cyan bold] [path]{top_path.name}[/path]")
        console.print(f"  [dim]{top_info.resolution_label} ({top_info.width}x{top_info.height}) | {top_info.video_codec} | {top_info.duration_formatted}[/dim]")

        console.print(f"\n  [cyan bold]Bottom Video (Comparison):[/cyan bold] [path]{bot_path.name}[/path]")
        console.print(f"  [dim]{bot_info.resolution_label} ({bot_info.width}x{bot_info.height}) | {bot_info.video_codec} | {bot_info.duration_formatted}[/dim]\n")

        # 1. Custom labels
        default_top = f"Top: {top_path.name}"
        default_bot = f"Bottom: {bot_path.name}"
        if inquirer.confirm(message="Customize labels on videos?", default=False).execute():
            params["top_label"] = inquirer.text(message="Top video label:", default=default_top).execute()
            params["bottom_label"] = inquirer.text(message="Bottom video label:", default=default_bot).execute()
        else:
            params["top_label"] = default_top
            params["bottom_label"] = default_bot

        # 2. Label Position
        params["label_position"] = inquirer.select(
            message="Label position at top of each video:",
            choices=[
                {"name": "Top-Left (Badge with dark pill) [Recommended]", "value": "top_left"},
                {"name": "Top-Center (Centered banner)", "value": "top_center"},
            ],
            default="top_left",
        ).execute()

        # 3. Target resolution
        w_max = max(top_info.width or 1280, bot_info.width or 1280)
        params["target_width"] = inquirer.select(
            message="Comparison collage width:",
            choices=[
                {"name": f"Auto / Maximum Width ({w_max}px) [Best for visual comparison]", "value": "max"},
                {"name": "1080p Width (1920px)", "value": "1080p"},
                {"name": "720p Width (1280px)", "value": "720p"},
            ],
            default="max",
        ).execute()

        # 4. Divider line
        params["divider_line"] = inquirer.confirm(
            message="Add colored divider line between videos?", default=True
        ).execute()

        # 5. Audio source
        audio_choices = [
            {"name": "Keep audio from Top video [Default]", "value": "top"},
            {"name": "Keep audio from Bottom video", "value": "bottom"},
            {"name": "Mix audio from both videos", "value": "mix"},
            {"name": "Mute (Silent comparison video)", "value": "mute"},
        ]
        params["audio_source"] = inquirer.select(
            message="Audio source for comparison video:",
            choices=audio_choices,
            default="top",
        ).execute()

        # 6. Quality (CRF)
        params["crf"] = inquirer.select(
            message="Collage video quality:",
            choices=[
                {"name": "Near Lossless (CRF 18) [Recommended for quality comparison]", "value": "18"},
                {"name": "Standard High (CRF 23)", "value": "23"},
            ],
            default="18",
        ).execute()

    return params


def show_main_menu():
    choices = []
    all_ops = get_all_operations()
    for label, name in CATEGORIES:
        count = sum(1 for op, _ in all_ops if op.category == name)
        choices.append({"name": f"{label}  ({count} ops)", "value": name})
    choices.append(Separator("-" * 40))
    choices.append({"name": "[R]  Recent Files", "value": "__RECENT__"})
    choices.append({"name": "[S]  Search all operations", "value": "__SEARCH__"})
    choices.append({"name": "[G]  Show GPU / Hardware info", "value": "__GPU_INFO__"})
    choices.append({"name": "[X]  Exit", "value": "__EXIT__"})
    return inquirer.select(message="Select a category:", choices=choices, default=None, pointer=">").execute()

def show_recent_files():
    recent = load_recent_files()
    if not recent:
        print_warning("No recent files found.")
        return None
    choices = []
    for r in recent:
        date_str = r.get("date", "")[:10]
        choices.append({"name": f"{date_str} | {Path(r['path']).name} ({r['op']})", "value": r['path']})
    choices.append(Separator("-" * 40))
    choices.append({"name": "<- Back", "value": "__BACK__"})
    return inquirer.select(message="Select a recent file:", choices=choices, pointer=">").execute()


def show_category_operations(category):
    ops = [(op, mod) for op, mod in get_all_operations() if op.category == category]
    if not ops:
        print_warning(f"No operations found in: {category}")
        return None
    choices = [{"name": f"[{op.id:>3}] {op.name}  -- {op.description}", "value": op.id} for op, _ in ops]
    choices.append(Separator("-" * 40))
    choices.append({"name": "<- Back to main menu", "value": "__BACK__"})
    return inquirer.select(message=f"Select operation ({category}):", choices=choices, pointer=">").execute()


def show_search_menu():
    choices = [{"name": f"[{op.id:>3}] [{op.category}] {op.name} -- {op.description}", "value": op.id} for op, _ in get_all_operations()]
    return inquirer.fuzzy(message="Search operations (type to filter):", choices=choices, pointer=">", max_height="70%").execute()


def show_gpu_info():
    from ffram.core.hardware import get_gpu_info
    info = get_gpu_info()
    table = Table(title="GPU and Hardware Acceleration", box=box.ROUNDED, border_style="bright_cyan")
    table.add_column("Feature", style="bright_cyan")
    table.add_column("Status", style="bright_white")
    table.add_row("NVIDIA NVENC", "[OK] Available" if info["nvidia_nvenc"] else "[--] Not found")
    table.add_row("Intel QuickSync", "[OK] Available" if info["intel_qsv"] else "[--] Not found")
    table.add_row("AMD AMF", "[OK] Available" if info["amd_amf"] else "[--] Not found")
    table.add_row("", "")
    table.add_row("Best H.264 Encoder", info["best_h264"])
    table.add_row("Best H.265 Encoder", info["best_h265"])
    if info["available_hw_encoders"]:
        table.add_row("", "")
        table.add_row("HW Encoders", ", ".join(info["available_hw_encoders"]))
    console.print(table)
    console.print()


def get_second_input_filters(op_info):
    types = set(op_info.second_input_types)
    if "video" in types and "audio" in types:
        return MEDIA_FILTERS
    if "video" in types:
        return VIDEO_FILTERS
    if "audio" in types:
        return AUDIO_FILTERS
    if "image" in types:
        return IMAGE_FILTERS
    if "subtitle" in types:
        return SUBTITLE_FILTERS
    return MEDIA_FILTERS


def execute_operation(operation_id, initial_file=None):
    target_op, target_module = None, None
    for op, mod in get_all_operations():
        if op.id == operation_id:
            target_op, target_module = op, mod
            break
    if not target_op:
        print_error(f"Operation {operation_id} not found.")
        return

    print_section(f"{target_op.name} -- {target_op.description}")
    params = {}

    # Batch needs directory
    if target_op.category == "Batch Processing":
        if initial_file and Path(initial_file).is_dir():
            directory = Path(initial_file)
            console.print(f"  [path]Selected folder: {directory}[/path]")
        else:
            directory = prompt_directory_input("Select folder with MP4 files")
            if not directory:
                print_warning("Operation cancelled.")
                return
        params["input_dir"] = directory
        params["input_path"] = str(directory)

    # Multi-file concat
    elif target_op.id in (73, 74):
        files = prompt_multi_file_input("Select video files to concatenate", VIDEO_FILTERS)
        if not files or len(files) < 2:
            print_warning("Need at least 2 files to concatenate.")
            return
        params["input_path"] = str(files[0])
        params["file_list"] = files
        params["duration"] = 0

    else:
        if initial_file and Path(initial_file).is_file():
            input_file = Path(initial_file)
            console.print(f"  [path]Selected file: {input_file}[/path]")
        else:
            if target_op.id == 103:
                prompt_title = "Select Target Video (receives audio)"
            elif target_op.id == 104:
                prompt_title = "Select Top Video (e.g. Reference / Original)"
            else:
                prompt_title = "Select input file"
            input_file = prompt_file_input(prompt_title)
            if not input_file:
                print_warning("Operation cancelled.")
                return
        params["input_path"] = str(input_file)
        try:
            info = probe(input_file)
            params["duration"] = info.duration
            console.print(f"  [dim]{info.resolution_label} | {info.video_codec} | {info.duration_formatted} | {info.size_formatted}[/dim]")
        except Exception:
            params["duration"] = 0

    # Second input
    if target_op.needs_second_input and "video_multi" not in target_op.second_input_types:
        filters = get_second_input_filters(target_op)
        second_file = prompt_file_input(target_op.second_input_label, filters)
        if not second_file:
            print_warning("Operation cancelled (second input required).")
            return
        params["second_input_path"] = str(second_file)

    params = prompt_operation_params(target_op, params)

    console.print()
    print_parameter_summary(target_op.name, params)
    
    if not inquirer.confirm(message="Execute this operation?", default=True).execute():
        print_warning("Operation cancelled by user.")
        return

    console.print()
    start_time = time.time()
    result = target_module.execute(target_op.id, params)
    elapsed_time = time.time() - start_time

    if result.success:
        print_success(result.message)
        if result.output_path:
            console.print(f"  [dim]-> Output: {result.output_path}[/dim]\n")
            
            # Print quick stats
            from ffram.core.hardware import get_gpu_info
            hw_info = get_gpu_info()
            gpu_accel = bool(hw_info["nvidia_nvenc"] or hw_info["intel_qsv"] or hw_info["amd_amf"])
            print_quick_stats(elapsed_time, gpu_accel)

            # Print IO Comparison and save report
            if target_op.category != "Batch Processing" and "input_path" in params:
                try:
                    in_info = probe(params["input_path"])
                    out_info = probe(result.output_path)
                    print_io_comparison(in_info, out_info)
                    
                    if inquirer.confirm(message="Save detailed markdown report?", default=False).execute():
                        generate_report(in_info, out_info, params, target_op.name, elapsed_time)
                        
                except Exception as e:
                    console.print(f"  [dim]Could not generate comparison: {e}[/dim]")
            
            if "input_path" in params and target_op.category != "Batch Processing":
                save_recent_file(params["input_path"], target_op.name)
    else:
        print_error(result.message)

    inquirer.text(message="Press Enter to continue...", default="").execute()
