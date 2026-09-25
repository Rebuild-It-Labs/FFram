"""Crop and aspect ratio operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class CropPadOps(BaseOperation):

    def get_operations(self):
        C = "Crop / Aspect Ratio"
        return [
            OperationInfo(81, "Crop to 1280x720", "Center crop to 1280x720", C),
            OperationInfo(82, "Crop to Square (1:1)", "Center crop to perfect square", C),
            OperationInfo(83, "Crop 16:9 to 9:16", "Convert landscape to vertical for Reels/Shorts", C),
            OperationInfo(84, "Crop 16:9 to 1:1", "Crop landscape to square for Instagram", C),
            OperationInfo(85, "Add Letterbox Bars", "Pad with black bars to 1920x1080", C),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        cmd_map = {
            81: (["-i", i, "-vf", "crop=1280:720"], "_cropped", ".mp4"),
            82: (["-i", i, "-vf", "crop=min(iw\\,ih):min(iw\\,ih)"], "_square", ".mp4"),
            83: (["-i", i, "-vf", "crop=ih*9/16:ih,scale=1080:1920"], "_vertical", ".mp4"),
            84: (["-i", i, "-vf", "crop=ih:ih,scale=1080:1080"], "_square_1080", ".mp4"),
            85: (["-i", i, "-vf", "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black"], "_letterbox", ".mp4"),
        }
        return self.run_map(operation_id, params, cmd_map, "Cropping")
