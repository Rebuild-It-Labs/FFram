"""
operations/subtitles.py - Subtitle operations (Operations 86-89).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class SubtitleOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(86, "Burn subtitles (hardcode SRT)", "Permanently burn SRT subtitles into video",
                          "Subtitles", needs_second_input=True,
                          second_input_label="SRT Subtitle File", second_input_types=["subtitle"]),
            OperationInfo(87, "Add selectable subtitle track", "Embed subtitle as toggleable stream",
                          "Subtitles", needs_second_input=True,
                          second_input_label="SRT Subtitle File", second_input_types=["subtitle"]),
            OperationInfo(88, "Extract subtitles to SRT", "Extract first subtitle stream to SRT file", "Subtitles"),
            OperationInfo(89, "[91] Remove All Subtitle Tracks from Video", "Strip all subtitle tracks from video", "Subtitles"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        if operation_id == 86:
            sub_path = Path(params["second_input_path"])
            output_path = params.get("output_path") or self._build_output_path(input_path, "_hardsubbed", ".mp4")
            # Escape Windows paths for subtitles filter (backslashes → forward slashes, colons escaped)
            sub_path_escaped = str(sub_path).replace("\\", "/").replace(":", "\\:")
            cmd_args = ["-i", str(input_path),
                        "-vf", f"subtitles='{sub_path_escaped}'",
                        str(output_path)]

        elif operation_id == 87:
            sub_path = Path(params["second_input_path"])
            output_path = params.get("output_path") or self._build_output_path(input_path, "_subtitled", ".mp4")
            cmd_args = ["-i", str(input_path), "-i", str(sub_path),
                        "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text",
                        str(output_path)]

        elif operation_id == 88:
            output_path = params.get("output_path") or self._build_output_path(input_path, "", ".srt")
            cmd_args = ["-i", str(input_path), "-map", "0:s:0", str(output_path)]

        elif operation_id == 89:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_nosubs", ".mkv")
            cmd_args = ["-i", str(input_path), "-map", "0:v", "-map", "0:a",
                        "-c", "copy", str(output_path)]
        else:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Processing subtitles")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Subtitles processed → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
