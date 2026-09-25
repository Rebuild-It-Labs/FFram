"""
operations/concat.py - Video concatenation and merging (Operations 73-75).
"""

import tempfile
from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class ConcatOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(73, "Concatenate videos (same codec)", "Lossless concat using demuxer", "Combine Videos",
                          needs_second_input=True, second_input_label="Video Files to Join",
                          second_input_types=["video_multi"]),
            OperationInfo(74, "Concatenate videos (different codecs)", "Re-encode and join different videos",
                          "Combine Videos", needs_second_input=True, second_input_label="Video Files to Join",
                          second_input_types=["video_multi"]),
            OperationInfo(75, "Join two videos (filter_complex)", "Concat two videos using filter",
                          "Combine Videos", needs_second_input=True, second_input_label="Second Video",
                          second_input_types=["video"]),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        if operation_id in (73, 74):
            # Multiple files - create concat list
            file_list = params.get("file_list", [input_path])
            if isinstance(file_list[0], str):
                file_list = [Path(f) for f in file_list]

            # Create temporary concat list file
            list_file = input_path.parent / "_concat_list.txt"
            with open(list_file, "w", encoding="utf-8") as f:
                for file in file_list:
                    # Use forward slashes and escape single quotes for ffmpeg
                    escaped = str(file).replace("\\", "/").replace("'", "'\\''")
                    f.write(f"file '{escaped}'\n")

            output_path = params.get("output_path") or self._build_output_path(input_path, "_merged", ".mp4")

            if operation_id == 73:
                cmd_args = ["-f", "concat", "-safe", "0", "-i", str(list_file),
                            "-c", "copy", str(output_path)]
            else:
                cmd_args = ["-f", "concat", "-safe", "0", "-i", str(list_file),
                            "-c:v", "libx264", "-c:a", "aac", str(output_path)]

            print_command(["ffmpeg", "-y"] + cmd_args)

            progress = FFmpegProgressBar(description="Merging videos")
            progress.start()

            result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

            # Clean up temp list file
            try:
                list_file.unlink()
            except OSError:
                pass

            if result.success:
                progress.finish()
                return OperationResult(
                    True,
                    f"Merged {len(file_list)} videos → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                    output_path, result.elapsed_seconds, result.command,
                )
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        elif operation_id == 75:
            second_input = Path(params["second_input_path"])
            output_path = params.get("output_path") or self._build_output_path(input_path, "_joined", ".mp4")

            cmd_args = [
                "-i", str(input_path), "-i", str(second_input),
                "-filter_complex",
                "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                "-map", "[v]", "-map", "[a]", str(output_path),
            ]

            print_command(["ffmpeg", "-y"] + cmd_args)

            progress = FFmpegProgressBar(description="Joining videos")
            progress.start()

            result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

            if result.success:
                progress.finish()
                return OperationResult(
                    True,
                    f"Joined → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                    output_path, result.elapsed_seconds, result.command,
                )
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

        return OperationResult(False, f"Unknown operation ID: {operation_id}")
