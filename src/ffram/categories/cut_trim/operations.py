"""
Video cutting and trimming operations.
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class CutTrimOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(38, "[38] Trim First N Seconds from Video (Instant Stream Copy)", "Keep only the first N seconds", "Cut / Trim"),
            OperationInfo(39, "Start at timestamp", "Remove beginning up to timestamp", "Cut / Trim"),
            OperationInfo(40, "Cut from A to B", "Extract clip between two timestamps", "Cut / Trim"),
            OperationInfo(41, "[41] Cut N-Second Clip Starting at Timestamp (Instant Stream Copy)", "Extract N seconds starting at timestamp", "Cut / Trim"),
            OperationInfo(42, "Accurate re-encoded cut", "Frame-accurate cut with re-encoding", "Cut / Trim"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        start_time = params.get("start_time", "00:00:00")
        end_time = params.get("end_time", "")
        cut_duration = params.get("cut_duration", "30")

        # Operation 42 re-encodes to MP4; stream copy operations (38-41) preserve original container
        if operation_id == 42:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_cut", ".mp4")
        else:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_cut")

        cmd_map = {
            38: ["-i", str(input_path), "-t", str(cut_duration),
                 "-c", "copy", str(output_path)],
            39: ["-ss", start_time, "-i", str(input_path),
                 "-c", "copy", str(output_path)],
            40: ["-ss", start_time, "-to", end_time, "-i", str(input_path),
                 "-c", "copy", str(output_path)],
            41: ["-ss", start_time, "-i", str(input_path), "-t", str(cut_duration),
                 "-c", "copy", str(output_path)],
            42: ["-ss", start_time, "-i", str(input_path), "-t", str(cut_duration),
                 "-c:v", "libx264", "-c:a", "aac", str(output_path)],
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args = cmd_map[operation_id]
        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Cutting")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Cut complete → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
