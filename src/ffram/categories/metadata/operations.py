"""
operations/metadata.py - Metadata and probe operations (Operations 90-93).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.core.probe import probe
from ffram.ui.console import print_media_info, print_command, format_elapsed


class MetadataOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(90, "Show media information", "Display detailed file/stream info (ffprobe)", "Metadata"),
            OperationInfo(91, "Remove all metadata", "Strip all metadata tags from file", "Metadata"),
            OperationInfo(92, "Set title metadata", "Set the video title tag", "Metadata"),
            OperationInfo(93, "Set artist metadata", "Set the artist/author tag", "Metadata"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        if operation_id == 90:
            try:
                info = probe(input_path)
                print_media_info(info)
                return OperationResult(True, "Media information displayed successfully.")
            except Exception as e:
                return OperationResult(False, f"Failed to probe: {e}")

        elif operation_id == 91:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_clean")
            cmd_args = ["-i", str(input_path), "-map_metadata", "-1",
                        "-c", "copy", str(output_path)]

        elif operation_id == 92:
            title = params.get("title", "My Video")
            output_path = params.get("output_path") or self._build_output_path(input_path, "_titled")
            cmd_args = ["-i", str(input_path),
                        "-metadata", f"title={title}",
                        "-c", "copy", str(output_path)]

        elif operation_id == 93:
            artist = params.get("artist", "Unknown")
            output_path = params.get("output_path") or self._build_output_path(input_path, "_tagged")
            cmd_args = ["-i", str(input_path),
                        "-metadata", f"artist={artist}",
                        "-c", "copy", str(output_path)]
        else:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        print_command(["ffmpeg", "-y"] + cmd_args)

        result = run_ffmpeg(cmd_args, duration=duration)

        if result.success:
            return OperationResult(
                True,
                f"Metadata updated → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
