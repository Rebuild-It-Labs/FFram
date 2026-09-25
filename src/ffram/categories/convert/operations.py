"""Video container conversion operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class ConvertOps(BaseOperation):

    def get_operations(self):
        C = "Video Conversion"
        return [
            OperationInfo(17, "Remux MP4 to MKV", "Lossless stream copy", C),
            OperationInfo(18, "Remux MKV to MP4", "Lossless stream copy", C),
            OperationInfo(19, "Convert MOV to MP4", "H.264 + AAC", C),
            OperationInfo(20, "Convert AVI to MP4", "H.264 + AAC", C),
            OperationInfo(21, "Convert WebM to MP4", "H.264 + AAC", C),
            OperationInfo(22, "Convert MP4 to WebM", "VP9 + Opus", C),
            OperationInfo(23, "Convert MP4 to MOV", "H.264 + AAC", C),
            OperationInfo(24, "Convert MP4 to AVI", "MPEG4 + MP3", C),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        cmd_map = {
            17: (["-i", i, "-c", "copy"], "_converted", ".mkv"),
            18: (["-i", i, "-c", "copy"], "_converted", ".mp4"),
            19: (["-i", i, "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mp4"),
            20: (["-i", i, "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mp4"),
            21: (["-i", i, "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mp4"),
            22: (["-i", i, "-c:v", "libvpx-vp9", "-c:a", "libopus"], "_converted", ".webm"),
            23: (["-i", i, "-c:v", "libx264", "-c:a", "aac"], "_converted", ".mov"),
            24: (["-i", i, "-c:v", "mpeg4", "-c:a", "mp3"], "_converted", ".avi"),
        }
        return self.run_map(operation_id, params, cmd_map, "Converting")
