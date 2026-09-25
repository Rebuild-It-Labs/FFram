"""Visual effects and filter operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class VideoFXOps(BaseOperation):

    def get_operations(self):
        V = "Video Effects"
        return [
            OperationInfo(54, "Rotate 90 Clockwise", "Rotate video 90 degrees CW", V),
            OperationInfo(55, "Rotate 90 Counter-Clockwise", "Rotate video 90 degrees CCW", V),
            OperationInfo(56, "Rotate 180", "Rotate video upside down", V),
            OperationInfo(57, "Flip Horizontally", "Mirror left-right", V),
            OperationInfo(58, "Flip Vertically", "Mirror top-bottom", V),
            OperationInfo(59, "Black and White", "Convert to grayscale", V),
            OperationInfo(60, "Blur Video", "Apply box blur effect", V),
            OperationInfo(61, "Sharpen Video", "Apply unsharp mask", V),
            OperationInfo(62, "Increase Brightness", "Brighten by 10%", V),
            OperationInfo(63, "Increase Contrast", "Boost contrast by 50%", V),
            OperationInfo(64, "Increase Saturation", "Boost color saturation by 50%", V),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        cmd_map = {
            54: (["-i", i, "-vf", "transpose=1"], "_rot90", ".mp4"),
            55: (["-i", i, "-vf", "transpose=2"], "_rot270", ".mp4"),
            56: (["-i", i, "-vf", "transpose=1,transpose=1"], "_rot180", ".mp4"),
            57: (["-i", i, "-vf", "hflip"], "_hflip", ".mp4"),
            58: (["-i", i, "-vf", "vflip"], "_vflip", ".mp4"),
            59: (["-i", i, "-vf", "format=gray"], "_bw", ".mp4"),
            60: (["-i", i, "-vf", "boxblur=10:1"], "_blur", ".mp4"),
            61: (["-i", i, "-vf", "unsharp=5:5:1.0"], "_sharp", ".mp4"),
            62: (["-i", i, "-vf", "eq=brightness=0.1"], "_bright", ".mp4"),
            63: (["-i", i, "-vf", "eq=contrast=1.5"], "_contrast", ".mp4"),
            64: (["-i", i, "-vf", "eq=saturation=1.5"], "_saturated", ".mp4"),
        }
        return self.run_map(operation_id, params, cmd_map, "Applying effect")
