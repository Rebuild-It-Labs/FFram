"""
operations/resize.py - Video resizing and scaling (Operations 31-37).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class ResizeOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(31, "Resize to 1280×720", "Scale to exact 1280×720 resolution", "Resize Video"),
            OperationInfo(32, "Resize to 1080p", "Scale height to 1080, keep aspect ratio", "Resize Video"),
            OperationInfo(33, "Resize to 720p", "Scale height to 720, keep aspect ratio", "Resize Video"),
            OperationInfo(34, "Resize to 480p", "Scale height to 480, keep aspect ratio", "Resize Video"),
            OperationInfo(35, "Resize to 4K (3840×2160)", "Upscale to 4K resolution", "Resize Video"),
            OperationInfo(36, "Resize width to 1280", "Scale width to 1280, keep aspect ratio", "Resize Video"),
            OperationInfo(37, "Resize to 720p + Compress", "Scale to 720p with CRF 28 compression", "Resize Video"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        cmd_map = {
            31: ["-i", str(input_path), "-vf", "scale=1280:720"],
            32: ["-i", str(input_path), "-vf", "scale=-2:1080"],
            33: ["-i", str(input_path), "-vf", "scale=-2:720"],
            34: ["-i", str(input_path), "-vf", "scale=-2:480"],
            35: ["-i", str(input_path), "-vf", "scale=3840:2160"],
            36: ["-i", str(input_path), "-vf", "scale=1280:-2"],
            37: ["-i", str(input_path), "-vf", "scale=-2:720",
                 "-c:v", "libx264", "-crf", "28", "-c:a", "aac"],
        }

        suffixes = {31: "_1280x720", 32: "_1080p", 33: "_720p", 34: "_480p",
                     35: "_4K", 36: "_w1280", 37: "_720p_compressed"}

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(
            input_path, suffixes[operation_id], ".mp4"
        )
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Resizing")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Resized → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
