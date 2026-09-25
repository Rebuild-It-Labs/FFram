"""Metadata inspection and editing operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class MetadataOps(BaseOperation):

    def get_operations(self):
        M = "Metadata"
        return [
            OperationInfo(90, "Show Media Info", "Display detailed file and stream info", M),
            OperationInfo(91, "Remove All Metadata", "Strip all metadata tags", M),
            OperationInfo(92, "Set Title Tag", "Set the video title metadata", M),
            OperationInfo(93, "Set Artist Tag", "Set the artist/author metadata", M),
        ]

    def execute(self, operation_id, params):
        input_path = Path(params["input_path"])
        i = str(input_path)
        duration = params.get("duration", 0)

        # Probe-only operation
        if operation_id == 90:
            try:
                from ffram.core.probe import probe
                from ffram.ui.console import print_media_info
                print_media_info(probe(input_path))
                return OperationResult(True, "Media information displayed.")
            except Exception as e:
                return OperationResult(False, f"Probe failed: {e}")

        if operation_id == 91:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_clean")
            cmd_args = ["-i", i, "-map_metadata", "-1", "-c", "copy", str(output_path)]
        elif operation_id == 92:
            title = params.get("title", "My Video")
            output_path = params.get("output_path") or self._build_output_path(input_path, "_titled")
            cmd_args = ["-i", i, "-metadata", f"title={title}", "-c", "copy", str(output_path)]
        elif operation_id == 93:
            artist = params.get("artist", "Unknown")
            output_path = params.get("output_path") or self._build_output_path(input_path, "_tagged")
            cmd_args = ["-i", i, "-metadata", f"artist={artist}", "-c", "copy", str(output_path)]
        else:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        return self.run_op(cmd_args, output_path, duration, "Updating metadata")
