"""Video to audio extraction operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class AudioExtractOps(BaseOperation):

    def get_operations(self):
        return [
            OperationInfo(1, "Extract Audio to MP3", "VBR ~190 kbps", "Video > Audio"),
            OperationInfo(2, "Extract Audio to WAV", "Lossless PCM 16-bit", "Video > Audio"),
            OperationInfo(3, "Extract Audio to AAC", "192 kbps", "Video > Audio"),
            OperationInfo(4, "Extract Audio to M4A", "AAC 192 kbps", "Video > Audio"),
            OperationInfo(5, "Extract Audio to FLAC", "Lossless", "Video > Audio"),
            OperationInfo(6, "Extract Audio to OGG", "Vorbis quality 5", "Video > Audio"),
            OperationInfo(7, "Extract Audio to OPUS", "128 kbps", "Video > Audio"),
            OperationInfo(8, "Extract Audio (Stream Copy)", "No re-encoding", "Video > Audio"),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        cmd_map = {
            1: (["-i", i, "-vn", "-c:a", "libmp3lame", "-q:a", "2"], "_audio", ".mp3"),
            2: (["-i", i, "-vn", "-c:a", "pcm_s16le"], "_audio", ".wav"),
            3: (["-i", i, "-vn", "-c:a", "aac", "-b:a", "192k"], "_audio", ".aac"),
            4: (["-i", i, "-vn", "-c:a", "aac", "-b:a", "192k"], "_audio", ".m4a"),
            5: (["-i", i, "-vn", "-c:a", "flac"], "_audio", ".flac"),
            6: (["-i", i, "-vn", "-c:a", "libvorbis", "-q:a", "5"], "_audio", ".ogg"),
            7: (["-i", i, "-vn", "-c:a", "libopus", "-b:a", "128k"], "_audio", ".opus"),
            8: (["-i", i, "-vn", "-c:a", "copy"], "_audio", ".m4a"),
        }
        return self.run_map(operation_id, params, cmd_map, "Extracting audio")
