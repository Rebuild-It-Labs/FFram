"""
operations/watermark.py - Overlay, watermark, and text operations (Operations 76-80).
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class WatermarkOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(76, "Add image watermark (top-left)", "Overlay logo at top-left corner",
                          "Overlay / Watermark", needs_second_input=True,
                          second_input_label="Watermark Image", second_input_types=["image"]),
            OperationInfo(77, "Watermark (bottom-right)", "Overlay logo at bottom-right corner",
                          "Overlay / Watermark", needs_second_input=True,
                          second_input_label="Watermark Image", second_input_types=["image"]),
            OperationInfo(78, "Semi-transparent watermark", "50% transparent watermark overlay",
                          "Overlay / Watermark", needs_second_input=True,
                          second_input_label="Watermark Image", second_input_types=["image"]),
            OperationInfo(79, "Add text overlay", "Burn text into video", "Overlay / Watermark"),
            OperationInfo(80, "Add timestamp overlay", "Burn running timecode into video", "Overlay / Watermark"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_watermarked", ".mp4")

        if operation_id == 76:
            logo_path = Path(params["second_input_path"])
            cmd_args = ["-i", str(input_path), "-i", str(logo_path),
                        "-filter_complex", "overlay=10:10", str(output_path)]

        elif operation_id == 77:
            logo_path = Path(params["second_input_path"])
            cmd_args = ["-i", str(input_path), "-i", str(logo_path),
                        "-filter_complex", "overlay=W-w-10:H-h-10", str(output_path)]

        elif operation_id == 78:
            logo_path = Path(params["second_input_path"])
            cmd_args = ["-i", str(input_path), "-i", str(logo_path),
                        "-filter_complex",
                        "[1:v]format=rgba,colorchannelmixer=aa=0.5[logo];[0:v][logo]overlay=10:10",
                        str(output_path)]

        elif operation_id == 79:
            text = params.get("text", "My Video")
            font_size = params.get("font_size", "40")
            font_color = params.get("font_color", "white")
            x_pos = params.get("x_pos", "50")
            y_pos = params.get("y_pos", "50")
            cmd_args = ["-i", str(input_path),
                        "-vf", f"drawtext=text='{text}':x={x_pos}:y={y_pos}:fontsize={font_size}:fontcolor={font_color}",
                        str(output_path)]

        elif operation_id == 80:
            cmd_args = ["-i", str(input_path),
                        "-vf", "drawtext=text='%{pts\\:hms}':x=20:y=20:fontsize=30:fontcolor=white",
                        str(output_path)]
        else:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Adding overlay")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Overlay added → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
