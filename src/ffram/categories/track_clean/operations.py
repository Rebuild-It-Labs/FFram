"""
operations/track_clean.py - Remove audio/video/subtitle tracks (Operations 43-45).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class TrackCleanOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(43, "Remove audio", "Strip all audio tracks from video", "Remove Tracks"),
            OperationInfo(44, "Remove video (audio only)", "Extract audio stream only", "Remove Tracks"),
            OperationInfo(45, "Create silent video", "Remove audio with re-encoding", "Remove Tracks"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        cmd_map = {
            43: (["-i", str(input_path), "-an", "-c:v", "copy"], "_noaudio", ".mp4"),
            44: (["-i", str(input_path), "-vn", "-c:a", "copy"], "_audioonly", ".m4a"),
            45: (["-i", str(input_path), "-an"], "_silent", ".mp4"),
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args, suffix, ext = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(input_path, suffix, ext)
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Removing tracks")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Tracks removed → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
