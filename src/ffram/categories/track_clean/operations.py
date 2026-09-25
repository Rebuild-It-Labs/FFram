"""Stream and track removal operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class TrackCleanOps(BaseOperation):

    def get_operations(self):
        R = "Remove Tracks"
        return [
            OperationInfo(43, "Remove Audio Track", "Strip all audio (stream copy)", R),
            OperationInfo(44, "Remove Video Track", "Keep audio only", R),
            OperationInfo(45, "Create Silent Video", "Remove audio with re-encoding", R),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        cmd_map = {
            43: (["-i", i, "-an", "-c:v", "copy"], "_noaudio", ".mp4"),
            44: (["-i", i, "-vn", "-c:a", "copy"], "_audioonly", ".m4a"),
            45: (["-i", i, "-an"], "_silent", ".mp4"),
        }
        return self.run_map(operation_id, params, cmd_map, "Removing tracks")
