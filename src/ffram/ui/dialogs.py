"""
ui/dialogs.py - Windows native file and folder picker dialogs.
Uses tkinter.filedialog with topmost window focus for guaranteed foreground.
"""

import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional


# File type filter presets
MEDIA_FILTERS = [
    ("All Media Files", "*.mp4;*.mkv;*.mov;*.avi;*.webm;*.mp3;*.wav;*.flac;*.m4a;*.aac;*.ogg;*.opus;*.gif;*.ts;*.flv"),
    ("Video Files", "*.mp4;*.mkv;*.mov;*.avi;*.webm;*.ts;*.flv;*.wmv;*.m4v;*.3gp"),
    ("Audio Files", "*.mp3;*.wav;*.aac;*.m4a;*.flac;*.ogg;*.opus;*.wma;*.ac3"),
    ("All Files", "*.*"),
]

VIDEO_FILTERS = [
    ("Video Files", "*.mp4;*.mkv;*.mov;*.avi;*.webm;*.ts;*.flv;*.wmv;*.m4v"),
    ("All Files", "*.*"),
]

AUDIO_FILTERS = [
    ("Audio Files", "*.mp3;*.wav;*.aac;*.m4a;*.flac;*.ogg;*.opus;*.wma"),
    ("All Files", "*.*"),
]

IMAGE_FILTERS = [
    ("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.tiff;*.webp"),
    ("All Files", "*.*"),
]

SUBTITLE_FILTERS = [
    ("Subtitle Files", "*.srt;*.ass;*.ssa;*.vtt;*.sub"),
    ("All Files", "*.*"),
]


def _create_root() -> tk.Tk:
    """Create a hidden Tk root window that stays on top."""
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    root.update()
    return root


def pick_file(
    title: str = "Select Media File",
    file_types: Optional[list] = None,
    initial_dir: Optional[str] = None,
) -> Optional[Path]:
    """
    Open a native Windows file open dialog.
    
    Args:
        title: Dialog window title.
        file_types: List of (label, pattern) tuples for filtering.
        initial_dir: Initial directory to open in.
    
    Returns:
        Selected file Path, or None if cancelled.
    """
    if file_types is None:
        file_types = MEDIA_FILTERS

    root = _create_root()
    try:
        file_path = filedialog.askopenfilename(
            title=title,
            filetypes=file_types,
            initialdir=initial_dir,
        )
    finally:
        root.destroy()

    return Path(file_path) if file_path else None


def pick_files(
    title: str = "Select Media Files",
    file_types: Optional[list] = None,
    initial_dir: Optional[str] = None,
) -> list[Path]:
    """
    Open a native Windows multi-file selection dialog.
    
    Returns:
        List of selected file Paths, or empty list if cancelled.
    """
    if file_types is None:
        file_types = MEDIA_FILTERS

    root = _create_root()
    try:
        file_paths = filedialog.askopenfilenames(
            title=title,
            filetypes=file_types,
            initialdir=initial_dir,
        )
    finally:
        root.destroy()

    return [Path(f) for f in file_paths] if file_paths else []


def pick_directory(
    title: str = "Select Directory",
    initial_dir: Optional[str] = None,
) -> Optional[Path]:
    """
    Open a native Windows directory selection dialog.
    
    Returns:
        Selected directory Path, or None if cancelled.
    """
    root = _create_root()
    try:
        dir_path = filedialog.askdirectory(
            title=title,
            initialdir=initial_dir,
        )
    finally:
        root.destroy()

    return Path(dir_path) if dir_path else None


def pick_save_file(
    title: str = "Save Output File",
    default_name: str = "output",
    default_extension: str = ".mp4",
    file_types: Optional[list] = None,
    initial_dir: Optional[str] = None,
) -> Optional[Path]:
    """
    Open a native Windows file save dialog.
    
    Returns:
        Selected save Path, or None if cancelled.
    """
    if file_types is None:
        file_types = [
            ("MP4 Video", "*.mp4"),
            ("MKV Video", "*.mkv"),
            ("MOV Video", "*.mov"),
            ("AVI Video", "*.avi"),
            ("WebM Video", "*.webm"),
            ("MP3 Audio", "*.mp3"),
            ("WAV Audio", "*.wav"),
            ("All Files", "*.*"),
        ]

    root = _create_root()
    try:
        file_path = filedialog.asksaveasfilename(
            title=title,
            defaultextension=default_extension,
            initialfile=default_name,
            filetypes=file_types,
            initialdir=initial_dir,
        )
    finally:
        root.destroy()

    return Path(file_path) if file_path else None
