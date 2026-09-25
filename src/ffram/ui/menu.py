"""Menu system."""

import sys
from pathlib import Path
from typing import Optional
from InquirerPy import inquirer
from InquirerPy.separator import Separator
from rich.console import Console
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

from ffram.core.validator import validate_input_file, validate_timestamp
from ffram.core.probe import probe
from ffram.ui.dialogs import pick_file, pick_files, pick_directory, MEDIA_FILTERS, VIDEO_FILTERS, AUDIO_FILTERS, IMAGE_FILTERS, SUBTITLE_FILTERS
from ffram.ui.console import console, print_success, print_error, print_warning, print_info, print_section


# Registry of all operation modules
OPERATION_MODULES = [
    AudioExtractOps(),
    AudioManageOps(),
    ConvertOps(),
    CompressOps(),
    ResizeOps(),
    CutTrimOps(),
    TrackCleanOps(),
    AudioFilterOps(),
    VideoFXOps(),
    SpeedOps(),
    ScreenshotGifOps(),
    ConcatOps(),
    WatermarkOps(),
    CropPadOps(),
    SubtitleOps(),
    MetadataOps(),
    BatchOps(),
    ComboOps(),
]

# Category definitions with icons
CATEGORIES = [
    ("[1]  Video > Audio", "Video → Audio"),
    ("[2]  Add / Replace Audio", "Add / Replace Audio"),
    ("[3]  Video Conversion", "Video Conversion"),
    ("[4]  Compress Video", "Compress Video"),
    ("[5]  Resize Video", "Resize Video"),
    ("[6]  Cut / Trim", "Cut / Trim"),
    ("[7]  Remove Tracks", "Remove Tracks"),
    ("[8]  Audio Processing", "Audio Processing"),
    ("[9]  Video Effects", "Video Effects"),
    ("[10] Video Speed", "Video Speed"),
    ("[11] Screenshots & GIF", "Screenshots & GIF"),
    ("[12] Combine Videos", "Combine Videos"),
    ("[13] Overlay / Watermark", "Overlay / Watermark"),
    ("[14] Crop / Aspect Ratio", "Crop / Aspect Ratio"),
    ("[15] Subtitles", "Subtitles"),
    ("[16] Metadata", "Metadata"),
    ("[17] Batch Processing", "Batch Processing"),
    ("[18] Smart Combos", "Smart Combos"),
]


def get_all_operations() -> list[tuple[OperationInfo, object]]:
    """Get all operations from all modules with their module references."""
    ops = []
    for module in OPERATION_MODULES:
        for op_info in module.get_operations():
            ops.append((op_info, module))
    return ops


def prompt_file_input(
    prompt_text: str = "Input file",
    file_types: Optional[list] = None,
    allow_browse: bool = True,
) -> Optional[Path]:
    """
    Prompt user for file input with browse support.
    - Press Enter (empty input) to open Windows file dialog
    - Type 'b' or 'browse' to open dialog
    - Paste/drag-and-drop a file path
    """
    while True:
        user_input = inquirer.text(
            message=f"{prompt_text} [Enter=Browse, or paste path]:",
            default="",
            validate=lambda _: True,  # Allow empty for browse
        ).execute()

        # Check for browse trigger
        if not user_input or user_input.strip().lower() in ("b", "browse"):
            if allow_browse:
                console.print("  [dim]Opening file picker...[/dim]")
                selected = pick_file(title=prompt_text, file_types=file_types or MEDIA_FILTERS)
                if selected:
                    console.print(f"  [path]Selected: {selected}[/path]")
                    return selected
                else:
                    print_warning("No file selected. Try again or type 'q' to cancel.")
                    continue
            else:
                print_warning("Please enter a file path.")
                continue

        # Check for quit
        if user_input.strip().lower() in ("q", "quit", "cancel"):
            return None

        # Validate the path
        valid, err, resolved = validate_input_file(user_input)
        if valid:
            return resolved
        else:
            print_error(err)
            continue


def prompt_multi_file_input(
    prompt_text: str = "Select files",
    file_types: Optional[list] = None,
) -> list[Path]:
    """Prompt for multiple file selection."""
    console.print(f"  [dim]{prompt_text} - Opening file picker for multiple files...[/dim]")
    files = pick_files(title=prompt_text, file_types=file_types or VIDEO_FILTERS)
    if files:
        console.print(f"  [path]Selected {len(files)} files[/path]")
    return files


def prompt_directory_input(prompt_text: str = "Select folder") -> Optional[Path]:
    """Prompt for directory selection."""
    user_input = inquirer.text(
        message=f"{prompt_text} [Enter=Browse]:",
        default="",
    ).execute()

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


def prompt_operation_params(op_info: OperationInfo, params: dict) -> dict:
    """Prompt for parameters."""
    category = op_info.category

    # Cut / Trim parameters
    if category == "Cut / Trim":
        if op_info.id in (38,):  # Cut first N seconds
            val = inquirer.text(
                message="Duration (seconds):",
                default="30",
            ).execute()
            params["cut_duration"] = val
        elif op_info.id in (39,):  # Start at timestamp
            val = inquirer.text(
                message="Start timestamp (HH:MM:SS or seconds):",
                default="00:01:00",
            ).execute()
            params["start_time"] = val
        elif op_info.id in (40,):  # From A to B
            params["start_time"] = inquirer.text(
                message="Start timestamp:", default="00:01:00",
            ).execute()
            params["end_time"] = inquirer.text(
                message="End timestamp:", default="00:02:30",
            ).execute()
        elif op_info.id in (41, 42):  # Cut N seconds
            params["start_time"] = inquirer.text(
                message="Start timestamp:", default="00:01:00",
            ).execute()
            params["cut_duration"] = inquirer.text(
                message="Duration (seconds):", default="30",
            ).execute()

    # Screenshot parameters
    elif op_info.id == 68:
        params["timestamp"] = inquirer.text(
            message="Screenshot timestamp (HH:MM:SS):",
            default="00:00:10",
        ).execute()

    # Watermark text parameters
    elif op_info.id == 79:
        params["text"] = inquirer.text(
            message="Text to overlay:",
            default="My Video",
        ).execute()
        params["font_size"] = inquirer.text(
            message="Font size:",
            default="40",
        ).execute()
        params["font_color"] = inquirer.select(
            message="Font color:",
            choices=["white", "yellow", "red", "green", "blue", "black"],
            default="white",
        ).execute()

    # Target size parameters
    elif op_info.id == 100:
        size = inquirer.select(
            message="Target file size:",
            choices=[
                {"name": "10 MB (Discord free)", "value": 10},
                {"name": "16 MB (WhatsApp)", "value": 16},
                {"name": "25 MB (Discord Nitro Basic)", "value": 25},
                {"name": "50 MB (Discord Nitro)", "value": 50},
                {"name": "100 MB (Email / Large)", "value": 100},
                {"name": "Custom size", "value": 0},
            ],
            default=25,
        ).execute()
        if size == 0:
            size = int(inquirer.text(message="Custom size in MB:", default="25").execute())
        params["target_size_mb"] = size

    # HQ GIF parameters
    elif op_info.id == 101:
        params["gif_fps"] = int(inquirer.text(
            message="GIF frame rate (fps):", default="15",
        ).execute())
        params["gif_width"] = int(inquirer.text(
            message="GIF width (pixels):", default="640",
        ).execute())

    # Multi-effect parameters
    elif op_info.id == 102:
        do_trim = inquirer.confirm(message="Trim video?", default=False).execute()
        if do_trim:
            params["trim_start"] = inquirer.text(
                message="Trim start:", default="00:00:00",
            ).execute()
            params["trim_end"] = inquirer.text(
                message="Trim end:", default="",
            ).execute()

        do_resize = inquirer.confirm(message="Resize video?", default=True).execute()
        if do_resize:
            params["resize_height"] = inquirer.select(
                message="Target resolution:",
                choices=[
                    {"name": "1080p", "value": "1080"},
                    {"name": "720p", "value": "720"},
                    {"name": "480p", "value": "480"},
                ],
                default="720",
            ).execute()

        do_watermark = inquirer.confirm(message="Add text watermark?", default=False).execute()
        if do_watermark:
            params["watermark_text"] = inquirer.text(
                message="Watermark text:", default="",
            ).execute()

        params["normalize_audio"] = inquirer.confirm(
            message="Normalize audio (EBU R128)?", default=True,
        ).execute()

        params["crf"] = inquirer.select(
            message="Compression quality:",
            choices=[
                {"name": "High (CRF 20)", "value": "20"},
                {"name": "Balanced (CRF 23)", "value": "23"},
                {"name": "Small (CRF 28)", "value": "28"},
            ],
            default="23",
        ).execute()

    # Metadata parameters
    elif op_info.id == 92:
        params["title"] = inquirer.text(message="Video title:", default="My Video").execute()
    elif op_info.id == 93:
        params["artist"] = inquirer.text(message="Artist name:", default="").execute()

    # Speed parameters (custom)
    elif category == "Video Speed":
        use_custom = inquirer.confirm(
            message="Use custom speed factor?", default=False,
        ).execute()
        if use_custom:
            params["speed_factor"] = float(inquirer.text(
                message="Speed factor (e.g., 3.0):", default="2.0",
            ).execute())

    return params


def show_main_menu():
    """Display the main interactive menu and return selected category."""
    choices = []
    for icon_name, internal_name in CATEGORIES:
        # Count operations in this category
        count = sum(
            1 for op, _ in get_all_operations()
            if op.category == internal_name
        )
        choices.append({"name": f"{icon_name}  ({count} ops)", "value": internal_name})

    choices.append(Separator("-" * 40))
    choices.append({"name": "[S]  Search all operations", "value": "__SEARCH__"})
    choices.append({"name": "[G]  Show GPU / Hardware info", "value": "__GPU_INFO__"})
    choices.append({"name": "[X]  Exit", "value": "__EXIT__"})

    return inquirer.select(
        message="Select a category:",
        choices=choices,
        default=None,
        pointer=">",
    ).execute()


def show_category_operations(category: str):
    """Display operations within a selected category."""
    ops = [(op, mod) for op, mod in get_all_operations() if op.category == category]

    if not ops:
        print_warning(f"No operations found in category: {category}")
        return None

    choices = [
        {"name": f"[{op.id:>3}] {op.name}  — {op.description}", "value": op.id}
        for op, _ in ops
    ]
    choices.append(Separator("-" * 40))
    choices.append({"name": "<- Back to main menu", "value": "__BACK__"})

    return inquirer.select(
        message=f"Select operation ({category}):",
        choices=choices,
        pointer=">",
    ).execute()


def show_search_menu():
    """Fuzzy-searchable list of all operations."""
    all_ops = get_all_operations()

    choices = [
        {"name": f"[{op.id:>3}] [{op.category}] {op.name} — {op.description}", "value": op.id}
        for op, _ in all_ops
    ]

    return inquirer.fuzzy(
        message="Search operations (type to filter):",
        choices=choices,
        pointer=">",
        max_height="70%",
    ).execute()


def show_gpu_info():
    """Display GPU / hardware acceleration info."""
    from ffram.core.hardware import get_gpu_info
    info = get_gpu_info()

    table = Table(
        title="GPU & Hardware Acceleration",
        box=box.ROUNDED,
        border_style="bright_cyan",
    )
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


def get_second_input_filters(op_info: OperationInfo) -> list:
    """Get appropriate file type filters for second input."""
    if "audio" in op_info.second_input_types:
        return AUDIO_FILTERS
    elif "image" in op_info.second_input_types:
        return IMAGE_FILTERS
    elif "subtitle" in op_info.second_input_types:
        return SUBTITLE_FILTERS
    elif "video" in op_info.second_input_types:
        return VIDEO_FILTERS
    return MEDIA_FILTERS


def execute_operation(operation_id: int, initial_file: Optional[Path] = None):
    """Full execution flow for a selected operation."""
    # Find the operation and its module
    target_op = None
    target_module = None
    for op, mod in get_all_operations():
        if op.id == operation_id:
            target_op = op
            target_module = mod
            break

    if not target_op:
        print_error(f"Operation {operation_id} not found.")
        return

    print_section(f"{target_op.name} — {target_op.description}")

    params = {}

    # Batch operations need directory input
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

    # Concat multi-file operations
    elif target_op.id in (73, 74):
        files = prompt_multi_file_input("Select video files to concatenate", VIDEO_FILTERS)
        if not files or len(files) < 2:
            print_warning("Need at least 2 files to concatenate.")
            return
        params["input_path"] = str(files[0])
        params["file_list"] = files
        params["duration"] = 0

    else:
        # Standard single-file input
        if initial_file and Path(initial_file).is_file():
            input_file = Path(initial_file)
            console.print(f"  [path]Selected file: {input_file}[/path]")
        else:
            input_file = prompt_file_input("Select input file")
            if not input_file:
                print_warning("Operation cancelled.")
                return
        params["input_path"] = str(input_file)

        # Probe for duration
        try:
            info = probe(input_file)
            params["duration"] = info.duration
            console.print(
                f"  [dim]{info.resolution_label} | {info.video_codec} | "
                f"{info.duration_formatted} | {info.size_formatted}[/dim]"
            )
        except Exception:
            params["duration"] = 0

    # Second input if needed
    if target_op.needs_second_input:
        if "video_multi" in target_op.second_input_types:
            pass  # Already handled above for concat
        else:
            filters = get_second_input_filters(target_op)
            second_file = prompt_file_input(target_op.second_input_label, filters)
            if not second_file:
                print_warning("Operation cancelled (second input required).")
                return
            params["second_input_path"] = str(second_file)

    # Prompt for operation-specific parameters
    params = prompt_operation_params(target_op, params)

    # Confirm execution
    console.print()
    proceed = inquirer.confirm(
        message="Execute this operation?",
        default=True,
    ).execute()

    if not proceed:
        print_warning("Operation cancelled by user.")
        return

    console.print()

    # Execute
    result = target_module.execute(target_op.id, params)

    if result.success:
        print_success(result.message)
        if result.output_path:
            console.print(f"  [dim]-> Output: {result.output_path}[/dim]\n")
    else:
        print_error(result.message)

    # Pause before returning to menu
    inquirer.text(message="Press Enter to continue...", default="").execute()
