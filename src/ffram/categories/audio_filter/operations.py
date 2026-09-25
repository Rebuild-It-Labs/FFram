"""
operations/audio_filter.py - Audio processing filters (Operations 46-53).
Volume, channels, sample rate, normalization, and fades.
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class AudioFilterOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(46, "Increase volume (2x)", "Double the audio volume", "Audio Processing"),
            OperationInfo(47, "Decrease volume (50%)", "Halve the audio volume", "Audio Processing"),
            OperationInfo(48, "Convert to mono", "Convert audio to single channel", "Audio Processing"),
            OperationInfo(49, "Convert to stereo", "Convert audio to two channels", "Audio Processing"),
            OperationInfo(50, "Change sample rate (44100 Hz)", "Resample audio to 44.1kHz", "Audio Processing"),
            OperationInfo(51, "Normalize audio (EBU R128)", "Loudness normalization to broadcast standard", "Audio Processing"),
            OperationInfo(52, "Fade audio in (3s)", "Fade audio in over 3 seconds", "Audio Processing"),
            OperationInfo(53, "Fade audio out (3s)", "Fade audio out over last 3 seconds", "Audio Processing"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        # For fade out, calculate start time
        fade_out_start = max(0, duration - 3) if duration > 3 else 0

        cmd_map = {
            46: (["-i", str(input_path), "-af", "volume=2", "-c:v", "copy"], "_loud"),
            47: (["-i", str(input_path), "-af", "volume=0.5", "-c:v", "copy"], "_quiet"),
            48: (["-i", str(input_path), "-ac", "1"], "_mono"),
            49: (["-i", str(input_path), "-ac", "2"], "_stereo"),
            50: (["-i", str(input_path), "-ar", "44100"], "_44100hz"),
            51: (["-i", str(input_path), "-af", "loudnorm", "-c:v", "copy"], "_normalized"),
            52: (["-i", str(input_path), "-af", "afade=t=in:st=0:d=3"], "_fadein"),
            53: (["-i", str(input_path), "-af", f"afade=t=out:st={fade_out_start}:d=3"], "_fadeout"),
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args, suffix = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(input_path, suffix, ".mp4")
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Processing audio")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Audio processed → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
