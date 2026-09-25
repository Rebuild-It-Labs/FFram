"""Video resizing and scaling operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class ResizeOps(BaseOperation):

    def get_operations(self):
        R = "Resize Video"
        return [
            OperationInfo(31, "Resize to 1280x720", "Scale to exact 1280x720", R),
            OperationInfo(32, "Resize to 1080p", "Scale height to 1080, keep aspect ratio", R),
            OperationInfo(33, "Resize to 720p", "Scale height to 720, keep aspect ratio", R),
            OperationInfo(34, "Resize to 480p", "Scale height to 480, keep aspect ratio", R),
            OperationInfo(35, "Resize to 4K", "Upscale to 3840x2160", R),
            OperationInfo(36, "Resize Width to 1280", "Scale width to 1280, keep aspect ratio", R),
            OperationInfo(37, "Resize to 720p + Compress", "Scale to 720p with CRF 28", R),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        cmd_map = {
            31: (["-i", i, "-vf", "scale=1280:720"], "_1280x720", ".mp4"),
            32: (["-i", i, "-vf", "scale=-2:1080"], "_1080p", ".mp4"),
            33: (["-i", i, "-vf", "scale=-2:720"], "_720p", ".mp4"),
            34: (["-i", i, "-vf", "scale=-2:480"], "_480p", ".mp4"),
            35: (["-i", i, "-vf", "scale=3840:2160"], "_4K", ".mp4"),
            36: (["-i", i, "-vf", "scale=1280:-2"], "_w1280", ".mp4"),
            37: (["-i", i, "-vf", "scale=-2:720", "-c:v", "libx264", "-crf", "28", "-c:a", "aac"], "_720p_compressed", ".mp4"),
        }
        return self.run_map(operation_id, params, cmd_map, "Resizing")
