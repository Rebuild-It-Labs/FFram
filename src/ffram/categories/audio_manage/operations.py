"""
operations/audio_manage.py - Add / Replace / Mix Audio (Operations 9-16).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class AudioManageOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(9, "Add audio to silent video", "Add audio track to a video with no audio",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="Audio File",
                          second_input_types=["audio"]),
            OperationInfo(10, "Add another audio track", "Add a second audio stream (keeps original)",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="Audio File",
                          second_input_types=["audio"]),
            OperationInfo(11, "Replace existing audio", "Replace the video's audio with a new file",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="New Audio File",
                          second_input_types=["audio"]),
            OperationInfo(12, "Add audio (keep original)", "Add another audio track while keeping original",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="Audio File",
                          second_input_types=["audio"]),
            OperationInfo(13, "Add audio (loop if shorter)", "Loop audio to match video length",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="Audio File",
                          second_input_types=["audio"]),
            OperationInfo(14, "Mix background music (keep voice)", "Mix music with original audio",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="Music File",
                          second_input_types=["audio"]),
            OperationInfo(15, "Mix background music at 20% vol", "Background music at reduced volume",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="Music File",
                          second_input_types=["audio"]),
            OperationInfo(16, "Replace audio (match duration)", "Replace audio, video matches audio length",
                          "Add / Replace Audio", needs_second_input=True, second_input_label="New Audio File",
                          second_input_types=["audio"]),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        second_input = Path(params["second_input_path"])
        duration = params.get("duration", 0)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_audio_edit", ".mp4")

        cmd_map = {
            9: ["-i", str(input_path), "-i", str(second_input),
                "-c:v", "copy", "-c:a", "aac", "-shortest", str(output_path)],
            10: ["-i", str(input_path), "-i", str(second_input),
                 "-map", "0:v", "-map", "0:a?", "-map", "1:a",
                 "-c:v", "copy", "-c:a", "aac", str(output_path)],
            11: ["-i", str(input_path), "-i", str(second_input),
                 "-map", "0:v:0", "-map", "1:a:0",
                 "-c:v", "copy", "-c:a", "aac", "-shortest", str(output_path)],
            12: ["-i", str(input_path), "-i", str(second_input),
                 "-map", "0:v", "-map", "0:a?", "-map", "1:a",
                 "-c:v", "copy", "-c:a", "aac", str(output_path)],
            13: ["-stream_loop", "-1", "-i", str(second_input),
                 "-i", str(input_path),
                 "-map", "1:v", "-map", "0:a",
                 "-c:v", "copy", "-c:a", "aac", "-shortest", str(output_path)],
            14: ["-i", str(input_path), "-i", str(second_input),
                 "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first",
                 "-c:v", "copy", "-c:a", "aac", str(output_path)],
            15: ["-i", str(input_path), "-i", str(second_input),
                 "-filter_complex", "[1:a]volume=0.2[m];[0:a][m]amix=inputs=2:duration=first",
                 "-c:v", "copy", "-c:a", "aac", str(output_path)],
            16: ["-i", str(input_path), "-i", str(second_input),
                 "-map", "0:v", "-map", "1:a",
                 "-c:v", "copy", "-c:a", "aac", "-shortest", str(output_path)],
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args = cmd_map[operation_id]
        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Processing audio")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Audio operation complete → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
