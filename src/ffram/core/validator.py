"""
core/validator.py - Path validation, format checking, and output path generation.
"""

import re
from pathlib import Path
from typing import Optional

# Supported media formats
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".ts", ".flv", ".wmv", ".m4v", ".3gp"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".aac", ".m4a", ".flac", ".ogg", ".opus", ".wma", ".ac3"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
SUBTITLE_EXTENSIONS = {".srt", ".ass", ".ssa", ".vtt", ".sub"}
ALL_MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | IMAGE_EXTENSIONS


def is_video(path: Path) -> bool:
    return path.suffix.lower() in VIDEO_EXTENSIONS


def is_audio(path: Path) -> bool:
    return path.suffix.lower() in AUDIO_EXTENSIONS


def is_image(path: Path) -> bool:
    return path.suffix.lower() in IMAGE_EXTENSIONS


def is_subtitle(path: Path) -> bool:
    return path.suffix.lower() in SUBTITLE_EXTENSIONS


def is_media(path: Path) -> bool:
    return path.suffix.lower() in ALL_MEDIA_EXTENSIONS


def validate_input_file(path_str: str) -> tuple[bool, str, Optional[Path]]:
    """
    Validate and sanitize an input file path from user input.
    Handles drag-and-drop edge cases on Windows:
    - Strips surrounding quotes
    - Strips PowerShell '& ' prefix
    - Normalizes backslashes
    
    Returns:
        (is_valid, error_message, resolved_path)
    """
    if not path_str or not path_str.strip():
        return False, "No file path provided.", None

    cleaned = path_str.strip()

    # Strip surrounding quotes (single or double)
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1]

    # Strip PowerShell drag-and-drop prefix: & 'path'
    if cleaned.startswith("& "):
        cleaned = cleaned[2:].strip()
        if (cleaned.startswith("'") and cleaned.endswith("'")) or \
           (cleaned.startswith('"') and cleaned.endswith('"')):
            cleaned = cleaned[1:-1]

    path = Path(cleaned)

    if not path.exists():
        return False, f"File not found: {path}", None

    if not path.is_file():
        return False, f"Not a file: {path}", None

    return True, "", path.resolve()


def validate_directory(path_str: str) -> tuple[bool, str, Optional[Path]]:
    """Validate a directory path."""
    if not path_str or not path_str.strip():
        return False, "No directory path provided.", None

    cleaned = path_str.strip().strip('"').strip("'")
    path = Path(cleaned)

    if not path.exists():
        return False, f"Directory not found: {path}", None

    if not path.is_dir():
        return False, f"Not a directory: {path}", None

    return True, "", path.resolve()


def generate_output_path(
    input_path: Path,
    suffix: str = "_output",
    new_extension: Optional[str] = None,
    output_dir: Optional[Path] = None,
) -> Path:
    """
    Generate an output file path that doesn't overwrite the input.
    
    Args:
        input_path: The input file path.
        suffix: Suffix to append to the filename (e.g., '_compressed', '_720p').
        new_extension: New file extension (e.g., '.mp3'). If None, keeps original.
        output_dir: Output directory. If None, uses the input file's directory.
    
    Returns:
        A unique output Path that doesn't conflict with existing files.
    """
    stem = input_path.stem
    ext = new_extension if new_extension else input_path.suffix
    if not ext.startswith("."):
        ext = "." + ext
    
    directory = output_dir if output_dir else input_path.parent

    output = directory / f"{stem}{suffix}{ext}"

    # If it already exists, append a number
    counter = 1
    while output.exists():
        output = directory / f"{stem}{suffix}_{counter}{ext}"
        counter += 1

    return output


def validate_timestamp(ts: str) -> tuple[bool, str]:
    """
    Validate a timestamp string in HH:MM:SS or HH:MM:SS.xxx format.
    Also accepts seconds as a plain number.
    """
    ts = ts.strip()

    # Plain number (seconds)
    if re.match(r"^\d+(\.\d+)?$", ts):
        return True, ""

    # HH:MM:SS or HH:MM:SS.xxx
    if re.match(r"^\d{1,2}:\d{2}:\d{2}(\.\d+)?$", ts):
        return True, ""

    # MM:SS
    if re.match(r"^\d{1,2}:\d{2}(\.\d+)?$", ts):
        return True, ""

    return False, f"Invalid timestamp format: '{ts}'. Use HH:MM:SS, MM:SS, or seconds."


def parse_timestamp_to_seconds(ts: str) -> float:
    """Convert a timestamp string to total seconds."""
    ts = ts.strip()

    if re.match(r"^\d+(\.\d+)?$", ts):
        return float(ts)

    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])

    return 0.0
