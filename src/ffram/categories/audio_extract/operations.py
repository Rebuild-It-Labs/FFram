"""
operations/audio_extract.py - Video to Audio extraction (Operations 1-8).
Supports MP3, WAV, AAC, M4A, FLAC, OGG, OPUS, and lossless stream copy.
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class AudioExtractOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(1, "[01] Extract Audio to MP3 (High-Quality VBR ~190 kbps)", "Extract audio as MP3 (VBR quality ~190kbps)", "Video → Audio"),
            OperationInfo(2, "[02] Extract Audio to WAV (Lossless PCM 16-bit)", "Extract audio as lossless WAV (PCM 16-bit)", "Video → Audio"),
            OperationInfo(3, "[03] Extract Audio to AAC (Standard 192 kbps)", "Extract audio as AAC (192kbps)", "Video → Audio"),
            OperationInfo(4, "[04] Extract Audio to M4A/AAC (Standard 192 kbps)", "Extract audio as M4A/AAC container (192kbps)", "Video → Audio"),
            OperationInfo(5, "[05] Extract Audio to FLAC (Lossless)", "Extract audio as lossless FLAC", "Video → Audio"),
            OperationInfo(6, "[06] Extract Audio to OGG Vorbis (Quality 5)", "Extract audio as OGG Vorbis (quality 5)", "Video → Audio"),
            OperationInfo(7, "[07] Extract Audio to OPUS (Web/Compact 96 kbps)", "Extract audio as OPUS (128kbps, excellent quality)", "Video → Audio"),
            OperationInfo(8, "Extract audio (no re-encode)", "Copy audio stream without re-encoding", "Video → Audio"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        cmd_map = {
            1: (
                ["-i", str(input_path), "-vn", "-c:a", "libmp3lame", "-q:a", "2"],
                "_audio", ".mp3"
            ),
            2: (
                ["-i", str(input_path), "-vn", "-c:a", "pcm_s16le"],
                "_audio", ".wav"
            ),
            3: (
                ["-i", str(input_path), "-vn", "-c:a", "aac", "-b:a", "192k"],
                "_audio", ".aac"
            ),
            4: (
                ["-i", str(input_path), "-vn", "-c:a", "aac", "-b:a", "192k"],
                "_audio", ".m4a"
            ),
            5: (
                ["-i", str(input_path), "-vn", "-c:a", "flac"],
                "_audio", ".flac"
            ),
            6: (
                ["-i", str(input_path), "-vn", "-c:a", "libvorbis", "-q:a", "5"],
                "_audio", ".ogg"
            ),
            7: (
                ["-i", str(input_path), "-vn", "-c:a", "libopus", "-b:a", "128k"],
                "_audio", ".opus"
            ),
            8: (
                ["-i", str(input_path), "-vn", "-c:a", "copy"],
                "_audio", ".m4a"
            ),
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args, suffix, ext = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(input_path, suffix, ext)
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description=f"Extracting {ext[1:].upper()}")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Audio extracted successfully → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path,
                result.elapsed_seconds,
                result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
