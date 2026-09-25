"""Audio track management operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class AudioManageOps(BaseOperation):

    def get_operations(self):
        A = "Audio Management"
        ai = {"needs_second_input": True, "second_input_label": "Audio File", "second_input_types": ["audio"]}
        return [
            OperationInfo(9, "Add Audio to Silent Video", "Mux audio into video with no audio", A, **ai),
            OperationInfo(10, "Add Second Audio Track", "Keep original, add extra audio stream", A, **ai),
            OperationInfo(11, "Replace Audio Track", "Swap existing audio with new file", A, **ai),
            OperationInfo(12, "Add Audio (Keep Original)", "Add track alongside original audio", A, **ai),
            OperationInfo(13, "Add Audio (Loop to Fit)", "Loop short audio to match video length", A, **ai),
            OperationInfo(14, "Mix Background Music", "Blend music with original audio", A, **ai),
            OperationInfo(15, "Mix Background Music (20%)", "Background music at 20% volume", A, **ai),
            OperationInfo(16, "Replace Audio (Match Length)", "Replace audio, trim video to audio length", A, **ai),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))
        a = str(Path(params["second_input_path"]))
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_audio_edit", ".mp4")
        o = str(output_path)

        cmd_map = {
            9:  ["-i", i, "-i", a, "-c:v", "copy", "-c:a", "aac", "-shortest", o],
            10: ["-i", i, "-i", a, "-map", "0:v", "-map", "0:a?", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", o],
            11: ["-i", i, "-i", a, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", o],
            12: ["-i", i, "-i", a, "-map", "0:v", "-map", "0:a?", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", o],
            13: ["-stream_loop", "-1", "-i", a, "-i", i, "-map", "1:v", "-map", "0:a", "-c:v", "copy", "-c:a", "aac", "-shortest", o],
            14: ["-i", i, "-i", a, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first", "-c:v", "copy", "-c:a", "aac", o],
            15: ["-i", i, "-i", a, "-filter_complex", "[1:a]volume=0.2[m];[0:a][m]amix=inputs=2:duration=first", "-c:v", "copy", "-c:a", "aac", o],
            16: ["-i", i, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", o],
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        return self.run_op(cmd_map[operation_id], output_path, duration, "Processing audio")
