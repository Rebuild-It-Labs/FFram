"""
operations/speed.py - Video speed adjustment (Operations 65-67).
Supports arbitrary speed factors with automatic atempo chaining for audio.
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class SpeedOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(65, "2× speed (fast forward)", "Double playback speed", "Video Speed"),
            OperationInfo(66, "0.5× slow motion", "Half speed slow motion", "Video Speed"),
            OperationInfo(67, "1.5× speed", "Play at 1.5x speed", "Video Speed"),
        ]

    def _build_atempo_chain(self, speed: float) -> str:
        """
        Build atempo filter chain. FFmpeg atempo supports 0.5-100.0 range,
        but for quality, we chain multiple atempo filters for extreme speeds.
        """
        filters = []
        remaining = speed
        while remaining > 2.0:
            filters.append("atempo=2.0")
            remaining /= 2.0
        while remaining < 0.5:
            filters.append("atempo=0.5")
            remaining /= 0.5
        filters.append(f"atempo={remaining}")
        return ",".join(filters)

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        speed_map = {65: 2.0, 66: 0.5, 67: 1.5}
        suffix_map = {65: "_2x", 66: "_slow", 67: "_1.5x"}

        if operation_id not in speed_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        speed = params.get("speed_factor", speed_map[operation_id])
        pts_factor = 1.0 / speed
        atempo = self._build_atempo_chain(speed)

        cmd_args = [
            "-i", str(input_path),
            "-filter_complex",
            f"[0:v]setpts={pts_factor}*PTS[v];[0:a]{atempo}[a]",
            "-map", "[v]", "-map", "[a]",
        ]

        output_path = params.get("output_path") or self._build_output_path(
            input_path, suffix_map.get(operation_id, f"_{speed}x"), ".mp4"
        )
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description=f"Adjusting speed to {speed}x")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Speed adjusted to {speed}x → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
