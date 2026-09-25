"""Screenshot extraction and GIF operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg


class ScreenshotGifOps(BaseOperation):

    def get_operations(self):
        S = "Screenshots / GIF"
        return [
            OperationInfo(68, "Single Screenshot", "Capture one frame at timestamp", S),
            OperationInfo(69, "Screenshot Every 10 Seconds", "Periodic frame extraction", S),
            OperationInfo(70, "Screenshot Every Second", "1 fps frame extraction", S),
            OperationInfo(71, "Video to GIF", "Animated GIF at 10 fps, 640px wide", S),
            OperationInfo(72, "GIF to MP4", "Convert animated GIF to video", S),
        ]

    def _extract_frames(self, input_path, fps_filter, suffix, ext, params):
        """Shared logic for periodic frame extraction."""
        output_dir = input_path.parent / f"{input_path.stem}_{suffix}"
        output_dir.mkdir(exist_ok=True)
        pattern = str(output_dir / f"frame_%04d{ext}")
        cmd_args = ["-i", str(input_path), "-vf", fps_filter, pattern]

        result = self.run_op(cmd_args, output_dir, params.get("duration", 0), "Extracting frames")
        if result.success:
            count = len(list(output_dir.glob(f"*{ext}")))
            result.message = f"Extracted {count} frames to {output_dir.name}/"
        return result

    def execute(self, operation_id, params):
        input_path = Path(params["input_path"])
        i = str(input_path)
        duration = params.get("duration", 0)

        if operation_id == 68:
            ts = params.get("timestamp", "00:00:10")
            output_path = params.get("output_path") or self._build_output_path(input_path, "_screenshot", ".png")
            cmd_args = ["-i", i, "-ss", ts, "-frames:v", "1", str(output_path)]
            from ffram.ui.console import print_command
            print_command(["ffmpeg", "-y"] + cmd_args)
            result = run_ffmpeg(cmd_args)
            if result.success:
                return OperationResult(True, f"Screenshot saved: {output_path.name}", output_path, result.elapsed_seconds, result.command)
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        if operation_id == 69:
            return self._extract_frames(input_path, "fps=1/10", "frames", ".png", params)
        if operation_id == 70:
            return self._extract_frames(input_path, "fps=1", "frames_1fps", ".jpg", params)

        if operation_id == 71:
            output_path = params.get("output_path") or self._build_output_path(input_path, "", ".gif")
            cmd_args = ["-i", i, "-vf", "fps=10,scale=640:-1", str(output_path)]
            return self.run_op(cmd_args, output_path, duration, "Creating GIF")

        if operation_id == 72:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_from_gif", ".mp4")
            cmd_args = ["-i", i, "-movflags", "faststart", "-pix_fmt", "yuv420p", str(output_path)]
            return self.run_op(cmd_args, output_path, duration, "Converting GIF to MP4")

        return OperationResult(False, f"Unknown operation ID: {operation_id}")
