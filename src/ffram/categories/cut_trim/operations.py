"""Video cutting and trimming operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class CutTrimOps(BaseOperation):

    def get_operations(self):
        C = "Cut / Trim"
        return [
            OperationInfo(38, "Trim First N Seconds", "Keep only the first N seconds (stream copy)", C),
            OperationInfo(39, "Trim from Timestamp", "Remove beginning up to timestamp (stream copy)", C),
            OperationInfo(40, "Cut Between Timestamps", "Extract clip between two timestamps (stream copy)", C),
            OperationInfo(41, "Cut N-Second Clip", "Extract N seconds starting at timestamp (stream copy)", C),
            OperationInfo(42, "Re-encode Cut (H.264)", "Frame-accurate cut with re-encoding", C),
        ]

    def execute(self, operation_id, params):
        input_path = Path(params["input_path"])
        i = str(input_path)
        start = params.get("start_time", "00:00:00")
        end = params.get("end_time", "")
        dur = params.get("cut_duration", "30")

        # Stream copy ops preserve container; re-encode defaults to .mp4
        ext = ".mp4" if operation_id == 42 else None
        output_path = params.get("output_path") or self._build_output_path(input_path, "_cut", ext)
        o = str(output_path)

        cmd_map = {
            38: ["-i", i, "-t", dur, "-c", "copy", o],
            39: ["-ss", start, "-i", i, "-c", "copy", o],
            40: ["-ss", start, "-to", end, "-i", i, "-c", "copy", o],
            41: ["-ss", start, "-i", i, "-t", dur, "-c", "copy", o],
            42: ["-ss", start, "-i", i, "-t", dur, "-c:v", "libx264", "-c:a", "aac", o],
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        return self.run_op(cmd_map[operation_id], output_path, params.get("duration", 0), "Cutting")
