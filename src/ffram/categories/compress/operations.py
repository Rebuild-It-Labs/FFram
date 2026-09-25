"""Video compression operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class CompressOps(BaseOperation):

    def get_operations(self):
        C = "Compress Video"
        return [
            OperationInfo(25, "Compress H.264 (CRF 28)", "Good balance of quality and size", C),
            OperationInfo(26, "Compress H.264 (CRF 20)", "Near-lossless visual quality", C),
            OperationInfo(27, "Compress H.264 (CRF 30)", "Smaller file, lower quality", C),
            OperationInfo(28, "Compress H.265 (CRF 28)", "50% smaller than H.264 at same quality", C),
            OperationInfo(29, "Compress H.265 (CRF 32)", "Maximum H.265 compression", C),
            OperationInfo(30, "Target Bitrate (1500 kbps)", "Compress to specific bitrate", C),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        cmd_map = {
            25: (["-i", i, "-c:v", "libx264", "-crf", "28", "-c:a", "aac", "-b:a", "128k"], "_compressed", ".mp4"),
            26: (["-i", i, "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "192k"], "_compressed", ".mp4"),
            27: (["-i", i, "-c:v", "libx264", "-crf", "30", "-c:a", "aac", "-b:a", "96k"], "_compressed", ".mp4"),
            28: (["-i", i, "-c:v", "libx265", "-crf", "28", "-c:a", "aac", "-b:a", "128k"], "_compressed", ".mp4"),
            29: (["-i", i, "-c:v", "libx265", "-crf", "32", "-c:a", "aac", "-b:a", "96k"], "_compressed", ".mp4"),
            30: (["-i", i, "-b:v", "1500k", "-c:a", "aac", "-b:a", "128k"], "_compressed", ".mp4"),
        }
        return self.run_map(operation_id, params, cmd_map, "Compressing")
