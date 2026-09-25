"""Video speed adjustment operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class SpeedOps(BaseOperation):

    def get_operations(self):
        S = "Video Speed"
        return [
            OperationInfo(65, "Speed Up 2x", "Double playback speed", S),
            OperationInfo(66, "Slow Motion 0.5x", "Half speed playback", S),
            OperationInfo(67, "Speed Up 1.5x", "1.5x playback speed", S),
        ]

    def _atempo_chain(self, speed):
        """Build chained atempo filter for speeds outside 0.5-2.0 range."""
        filters = []
        r = speed
        while r > 2.0:
            filters.append("atempo=2.0"); r /= 2.0
        while r < 0.5:
            filters.append("atempo=0.5"); r /= 0.5
        filters.append(f"atempo={r}")
        return ",".join(filters)

    def execute(self, operation_id, params):
        input_path = Path(params["input_path"])
        i = str(input_path)
        speeds = {65: 2.0, 66: 0.5, 67: 1.5}
        suffixes = {65: "_2x", 66: "_slow", 67: "_1.5x"}

        if operation_id not in speeds:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        speed = params.get("speed_factor", speeds[operation_id])
        pts = 1.0 / speed
        atempo = self._atempo_chain(speed)

        output_path = params.get("output_path") or self._build_output_path(
            input_path, suffixes.get(operation_id, f"_{speed}x"), ".mp4"
        )

        cmd_args = [
            "-i", i, "-filter_complex",
            f"[0:v]setpts={pts}*PTS[v];[0:a]{atempo}[a]",
            "-map", "[v]", "-map", "[a]", str(output_path),
        ]
        return self.run_op(cmd_args, output_path, params.get("duration", 0), f"Speed {speed}x")
