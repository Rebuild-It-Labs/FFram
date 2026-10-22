"""Base classes for all ffram operations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class OperationResult:
    success: bool
    message: str
    output_path: Optional[Path] = None
    elapsed_seconds: float = 0.0
    command: str = ""


@dataclass
class OperationInfo:
    id: int
    name: str
    description: str
    category: str
    needs_second_input: bool = False
    second_input_label: str = ""
    second_input_types: list = field(default_factory=list)


class BaseOperation(ABC):

    @abstractmethod
    def get_operations(self) -> list[OperationInfo]:
        pass

    @abstractmethod
    def execute(self, operation_id: int, params: dict) -> OperationResult:
        pass

    def _build_output_path(self, input_path: Path, suffix: str, new_ext: str = None) -> Path:
        ext = new_ext if new_ext else input_path.suffix
        if not ext.startswith("."):
            ext = "." + ext
        output = input_path.parent / f"{input_path.stem}{suffix}{ext}"
        counter = 1
        while output.exists():
            output = input_path.parent / f"{input_path.stem}{suffix}_{counter}{ext}"
            counter += 1
        return output

    def _sanitize_muxing_args(self, cmd_args: list[str], output_path: Optional[Path]) -> list[str]:
        """Automatically optimize container interleaving, buffer queues, and streaming headers."""
        if not output_path or not cmd_args:
            return cmd_args

        ext = output_path.suffix.lower()
        args = list(cmd_args)

        has_output_at_end = (args[-1] == str(output_path))
        target_args = args[:-1] if has_output_at_end else args

        has_multiple_inputs = (target_args.count("-i") > 1)
        has_stream_copy = any(
            "-c" in a or "-c:v" in a or "-c:a" in a or "-c:s" in a
            for a in target_args
        ) and "copy" in target_args

        # 1. MP4 / MOV faststart optimization for instant playback and seeking
        if ext in [".mp4", ".m4v", ".mov"]:
            if "-movflags" not in target_args:
                target_args.extend(["-movflags", "+faststart"])

        # 2. Prevent de-interleaving and audio/video starvation on multi-input or stream-copied media
        if ext in [".mkv", ".mp4", ".m4v", ".mov", ".webm", ".avi"]:
            if has_multiple_inputs or has_stream_copy:
                if "-max_interleave_delta" not in target_args:
                    target_args.extend(["-max_interleave_delta", "0"])
                if "-max_muxing_queue_size" not in target_args:
                    target_args.extend(["-max_muxing_queue_size", "2048"])

        if has_output_at_end:
            target_args.append(str(output_path))
        return target_args

    def run_op(self, cmd_args, output_path, duration=0, desc="Processing"):
        """Run ffmpeg with progress bar and return OperationResult."""
        from ffram.core.runner import run_ffmpeg
        from ffram.ui.progress_bar import FFmpegProgressBar
        from ffram.ui.console import print_command, format_elapsed

        cmd_args = self._sanitize_muxing_args(cmd_args, output_path)

        print_command(["ffmpeg", "-y"] + cmd_args)
        progress = FFmpegProgressBar(description=desc)
        progress.start()
        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            name = output_path.name if output_path else ""
            msg = f"{name} ({format_elapsed(result.elapsed_seconds)})" if name else f"Done ({format_elapsed(result.elapsed_seconds)})"
            return OperationResult(True, msg, output_path, result.elapsed_seconds, result.command)

        progress.error()
        return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

    def run_map(self, operation_id, params, cmd_map, desc="Processing", default_ext=None):
        """Map-driven executor: look up operation_id in cmd_map and run it."""
        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        entry = cmd_map[operation_id]

        cmd_args = list(entry[0])
        suffix = entry[1]
        ext = entry[2] if len(entry) > 2 else default_ext

        output_path = params.get("output_path") or self._build_output_path(input_path, suffix, ext)
        cmd_args.append(str(output_path))

        return self.run_op(cmd_args, output_path, duration, desc)
