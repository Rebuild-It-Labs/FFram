"""
operations/video_fx.py - Video effects (Operations 54-64).
Rotation, flips, grayscale, blur, sharpen, brightness, contrast, saturation.
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class VideoFXOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(54, "Rotate 90° clockwise", "Rotate video 90 degrees CW", "Video Effects"),
            OperationInfo(55, "Rotate 90° counter-clockwise", "Rotate video 90 degrees CCW", "Video Effects"),
            OperationInfo(56, "Rotate 180°", "Rotate video upside down", "Video Effects"),
            OperationInfo(57, "Flip horizontally", "Mirror the video left-right", "Video Effects"),
            OperationInfo(58, "Flip vertically", "Mirror the video top-bottom", "Video Effects"),
            OperationInfo(59, "Black & white", "Convert video to grayscale", "Video Effects"),
            OperationInfo(60, "Blur video", "Apply box blur effect", "Video Effects"),
            OperationInfo(61, "Sharpen video", "Apply unsharp mask for sharpening", "Video Effects"),
            OperationInfo(62, "Increase brightness", "Brighten video by 10%", "Video Effects"),
            OperationInfo(63, "Increase contrast", "Boost contrast by 50%", "Video Effects"),
            OperationInfo(64, "Adjust saturation", "Increase color saturation by 50%", "Video Effects"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        cmd_map = {
            54: (["-i", str(input_path), "-vf", "transpose=1"], "_rot90"),
            55: (["-i", str(input_path), "-vf", "transpose=2"], "_rot270"),
            56: (["-i", str(input_path), "-vf", "transpose=1,transpose=1"], "_rot180"),
            57: (["-i", str(input_path), "-vf", "hflip"], "_hflip"),
            58: (["-i", str(input_path), "-vf", "vflip"], "_vflip"),
            59: (["-i", str(input_path), "-vf", "format=gray"], "_bw"),
            60: (["-i", str(input_path), "-vf", "boxblur=10:1"], "_blur"),
            61: (["-i", str(input_path), "-vf", "unsharp=5:5:1.0"], "_sharp"),
            62: (["-i", str(input_path), "-vf", "eq=brightness=0.1"], "_bright"),
            63: (["-i", str(input_path), "-vf", "eq=contrast=1.5"], "_contrast"),
            64: (["-i", str(input_path), "-vf", "eq=saturation=1.5"], "_saturated"),
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args, suffix = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(input_path, suffix, ".mp4")
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Applying effects")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Effect applied → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
