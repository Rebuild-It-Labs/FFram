"""Audio processing filter operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class AudioFilterOps(BaseOperation):

    def get_operations(self):
        A = "Audio Processing"
        return [
            OperationInfo(46, "Volume Up (2x)", "Double the audio volume", A),
            OperationInfo(47, "Volume Down (50%)", "Halve the audio volume", A),
            OperationInfo(48, "Convert to Mono", "Single channel audio", A),
            OperationInfo(49, "Convert to Stereo", "Two channel audio", A),
            OperationInfo(50, "Resample to 44100 Hz", "Change sample rate to 44.1 kHz", A),
            OperationInfo(51, "Normalize Audio (EBU R128)", "Broadcast standard loudness", A),
            OperationInfo(52, "Fade In (3 seconds)", "Gradual audio fade in", A),
            OperationInfo(53, "Fade Out (3 seconds)", "Gradual audio fade out", A),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        duration = params.get("duration", 0)
        fade_start = max(0, duration - 3) if duration > 3 else 0

        cmd_map = {
            46: (["-i", i, "-af", "volume=2", "-c:v", "copy", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart"], "_loud", ".mp4"),
            47: (["-i", i, "-af", "volume=0.5", "-c:v", "copy", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart"], "_quiet", ".mp4"),
            48: (["-i", i, "-ac", "1", "-movflags", "+faststart"], "_mono", ".mp4"),
            49: (["-i", i, "-ac", "2", "-movflags", "+faststart"], "_stereo", ".mp4"),
            50: (["-i", i, "-ar", "44100", "-movflags", "+faststart"], "_44100hz", ".mp4"),
            51: (["-i", i, "-af", "loudnorm", "-c:v", "copy", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart"], "_normalized", ".mp4"),
            52: (["-i", i, "-af", "afade=t=in:st=0:d=3", "-movflags", "+faststart"], "_fadein", ".mp4"),
            53: (["-i", i, "-af", f"afade=t=out:st={fade_start}:d=3", "-movflags", "+faststart"], "_fadeout", ".mp4"),
        }
        return self.run_map(operation_id, params, cmd_map, "Processing audio")
