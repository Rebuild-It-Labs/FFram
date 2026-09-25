"""Subtitle embedding and extraction operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult

SUB = {"needs_second_input": True, "second_input_label": "SRT Subtitle File", "second_input_types": ["subtitle"]}


class SubtitleOps(BaseOperation):

    def get_operations(self):
        S = "Subtitles"
        return [
            OperationInfo(86, "Burn Subtitles (Hardsub)", "Permanently burn SRT into video", S, **SUB),
            OperationInfo(87, "Embed Subtitle Track", "Add toggleable subtitle stream", S, **SUB),
            OperationInfo(88, "Extract Subtitles to SRT", "Extract first subtitle stream", S),
            OperationInfo(89, "Remove All Subtitles", "Strip all subtitle tracks", S),
        ]

    def execute(self, operation_id, params):
        input_path = Path(params["input_path"])
        i = str(input_path)
        duration = params.get("duration", 0)

        if operation_id == 86:
            sub = str(Path(params["second_input_path"])).replace("\\", "/").replace(":", "\\:")
            output_path = params.get("output_path") or self._build_output_path(input_path, "_hardsubbed", ".mp4")
            cmd_args = ["-i", i, "-vf", f"subtitles='{sub}'", str(output_path)]
        elif operation_id == 87:
            sub = str(Path(params["second_input_path"]))
            output_path = params.get("output_path") or self._build_output_path(input_path, "_subtitled", ".mp4")
            cmd_args = ["-i", i, "-i", sub, "-c:v", "copy", "-c:a", "copy", "-c:s", "mov_text", str(output_path)]
        elif operation_id == 88:
            output_path = params.get("output_path") or self._build_output_path(input_path, "", ".srt")
            cmd_args = ["-i", i, "-map", "0:s:0", str(output_path)]
        elif operation_id == 89:
            output_path = params.get("output_path") or self._build_output_path(input_path, "_nosubs", ".mkv")
            cmd_args = ["-i", i, "-map", "0:v", "-map", "0:a", "-c", "copy", str(output_path)]
        else:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        return self.run_op(cmd_args, output_path, duration, "Processing subtitles")
