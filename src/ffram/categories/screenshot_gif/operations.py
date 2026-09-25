"""
operations/screenshot_gif.py - Screenshots and GIF operations (Operations 68-72).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class ScreenshotGifOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(68, "Extract one frame (screenshot)", "Capture a single frame at timestamp", "Screenshots & GIF"),
            OperationInfo(69, "Extract frame every 10 seconds", "Periodic screenshots every 10s", "Screenshots & GIF"),
            OperationInfo(70, "Extract one frame per second", "Screenshot every second (1 fps)", "Screenshots & GIF"),
            OperationInfo(71, "[71] Convert Video to Animated GIF (10fps, 640px wide)", "Convert video to GIF (10fps, 640px wide)", "Screenshots & GIF"),
            OperationInfo(72, "[72] Convert Animated GIF to MP4 Video", "Convert GIF to MP4 video", "Screenshots & GIF"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        timestamp = params.get("timestamp", "00:00:10")

        if operation_id == 68:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_screenshot", ".png")
            cmd_args = ["-i", str(input_path), "-ss", timestamp, "-frames:v", "1", str(output_path)]

            print_command(["ffmpeg", "-y"] + cmd_args)
            result = run_ffmpeg(cmd_args)

            if result.success:
                return OperationResult(True, f"Screenshot saved → {output_path.name}", output_path,
                                       result.elapsed_seconds, result.command)
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        elif operation_id == 69:
            output_dir = input_path.parent / f"{input_path.stem}_frames"
            output_dir.mkdir(exist_ok=True)
            output_pattern = str(output_dir / "frame_%04d.png")
            cmd_args = ["-i", str(input_path), "-vf", "fps=1/10", output_pattern]

            print_command(["ffmpeg", "-y"] + cmd_args)
            progress = FFmpegProgressBar(description="Extracting frames")
            progress.start()
            result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

            if result.success:
                progress.finish()
                frame_count = len(list(output_dir.glob("*.png")))
                return OperationResult(True, f"Extracted {frame_count} frames → {output_dir.name}/",
                                       output_dir, result.elapsed_seconds, result.command)
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        elif operation_id == 70:
            output_dir = input_path.parent / f"{input_path.stem}_frames_1fps"
            output_dir.mkdir(exist_ok=True)
            output_pattern = str(output_dir / "frame_%04d.jpg")
            cmd_args = ["-i", str(input_path), "-vf", "fps=1", output_pattern]

            print_command(["ffmpeg", "-y"] + cmd_args)
            progress = FFmpegProgressBar(description="Extracting frames (1 fps)")
            progress.start()
            result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

            if result.success:
                progress.finish()
                frame_count = len(list(output_dir.glob("*.jpg")))
                return OperationResult(True, f"Extracted {frame_count} frames → {output_dir.name}/",
                                       output_dir, result.elapsed_seconds, result.command)
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        elif operation_id == 71:
            output_path = params.get("output_path") or self._build_output_path(input_path, "", ".gif")
            cmd_args = ["-i", str(input_path), "-vf", "fps=10,scale=640:-1", str(output_path)]

            print_command(["ffmpeg", "-y"] + cmd_args)
            progress = FFmpegProgressBar(description="Creating GIF")
            progress.start()
            result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

            if result.success:
                progress.finish()
                return OperationResult(True, f"GIF created → {output_path.name}",
                                       output_path, result.elapsed_seconds, result.command)
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        elif operation_id == 72:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_from_gif", ".mp4")
            cmd_args = ["-i", str(input_path), "-movflags", "faststart",
                        "-pix_fmt", "yuv420p", str(output_path)]

            print_command(["ffmpeg", "-y"] + cmd_args)
            progress = FFmpegProgressBar(description="Converting GIF to MP4")
            progress.start()
            result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

            if result.success:
                progress.finish()
                return OperationResult(True, f"Converted → {output_path.name}",
                                       output_path, result.elapsed_seconds, result.command)
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        return OperationResult(False, f"Unknown operation ID: {operation_id}")
