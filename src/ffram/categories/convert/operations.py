"""
operations/convert.py - Video container conversion (Operations 17-24).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class ConvertOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(17, "[17] Remux MP4 to MKV Container (Lossless Stream Copy)", "Remux MP4 to MKV (no re-encoding)", "Video Conversion"),
            OperationInfo(18, "[18] Remux MKV to MP4 Container (Lossless Stream Copy)", "Remux MKV to MP4 (no re-encoding)", "Video Conversion"),
            OperationInfo(19, "[19] Convert MOV to MP4 (H.264 + AAC)", "Convert MOV to MP4 (H.264 + AAC)", "Video Conversion"),
            OperationInfo(20, "[20] Convert AVI to MP4 (H.264 + AAC)", "Convert AVI to MP4 (H.264 + AAC)", "Video Conversion"),
            OperationInfo(21, "[21] Convert WebM to MP4 (H.264 + AAC)", "Convert WebM to MP4 (H.264 + AAC)", "Video Conversion"),
            OperationInfo(22, "[22] Convert MP4 to WebM (VP9 + Opus)", "Convert MP4 to WebM (VP9 + Opus)", "Video Conversion"),
            OperationInfo(23, "[23] Convert MP4 to MOV (H.264 + AAC)", "Convert MP4 to MOV (H.264 + AAC)", "Video Conversion"),
            OperationInfo(24, "[24] Convert MP4 to AVI (MPEG4 + MP3)", "Convert MP4 to AVI (MPEG4 + MP3)", "Video Conversion"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        cmd_map = {
            17: (["-i", str(input_path), "-c", "copy"], "_converted", ".mkv"),
            18: (["-i", str(input_path), "-c", "copy"], "_converted", ".mp4"),
            19: (["-i", str(input_path), "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mp4"),
            20: (["-i", str(input_path), "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mp4"),
            21: (["-i", str(input_path), "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mp4"),
            22: (["-i", str(input_path), "-c:v", "libvpx-vp9", "-c:a", "libopus"], "_converted", ".webm"),
            23: (["-i", str(input_path), "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mov"),
            24: (["-i", str(input_path), "-c:v", "mpeg4", "-c:a", "mp3"], "_converted", ".avi"),
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args, suffix, ext = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(input_path, suffix, ext)
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description=f"Converting to {ext[1:].upper()}")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Converted → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
