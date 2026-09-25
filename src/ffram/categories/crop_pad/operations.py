"""
operations/crop_pad.py - Crop and aspect ratio operations (Operations 81-85).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class CropPadOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(81, "Crop video (1280×720)", "Crop to 1280×720 from center", "Crop / Aspect Ratio"),
            OperationInfo(82, "Center crop to square (1:1)", "Crop to perfect square from center", "Crop / Aspect Ratio"),
            OperationInfo(83, "[83] Crop 16:9 Landscape to 9:16 Vertical (Reels/Shorts)", "Convert landscape to portrait", "Crop / Aspect Ratio"),
            OperationInfo(84, "[84] Crop 16:9 Landscape to 1:1 Square (Instagram)", "Crop landscape to square", "Crop / Aspect Ratio"),
            OperationInfo(85, "Add black bars (letterbox)", "Pad video with black bars to 1920×1080", "Crop / Aspect Ratio"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        cmd_map = {
            81: (["-i", str(input_path), "-vf", "crop=1280:720"], "_cropped"),
            82: (["-i", str(input_path), "-vf", "crop=min(iw\\,ih):min(iw\\,ih)"], "_square"),
            83: (["-i", str(input_path), "-vf", "crop=ih*9/16:ih,scale=1080:1920"], "_vertical"),
            84: (["-i", str(input_path), "-vf", "crop=ih:ih,scale=1080:1080"], "_square_1080"),
            85: (["-i", str(input_path), "-vf", "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"], "_letterbox"),
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args, suffix = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(input_path, suffix, ".mp4")
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Cropping / Padding")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Crop/pad complete → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
