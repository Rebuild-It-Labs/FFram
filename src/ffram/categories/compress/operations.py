"""
operations/compress.py - Video compression (Operations 25-30).
Includes CRF presets, H.265, target bitrate, and Discord/WhatsApp target size mode.
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed


class CompressOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(25, "[25] Basic Video Compression (CRF 28 - Web/Compact)", "Good balance of quality and size", "Compress Video"),
            OperationInfo(26, "[26] High-Quality Compression (CRF 20 - Near Lossless)", "Near-lossless visual quality", "Compress Video"),
            OperationInfo(27, "[27] Maximum Compression (CRF 30 - Very Small)", "Smaller file, lower quality", "Compress Video"),
            OperationInfo(28, "[28] H.265/HEVC Compression (CRF 28 - 50% smaller than H.264)", "50% smaller than H.264 at same quality", "Compress Video"),
            OperationInfo(29, "[29] H.265/HEVC Maximum Compression (CRF 32)", "Maximum H.265 compression", "Compress Video"),
            OperationInfo(30, "[30] Target Bitrate Compression (1500 kbps)", "Compress to specific bitrate", "Compress Video"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        cmd_map = {
            25: ["-i", str(input_path), "-c:v", "libx264", "-crf", "28",
                 "-c:a", "aac", "-b:a", "128k"],
            26: ["-i", str(input_path), "-c:v", "libx264", "-crf", "20",
                 "-preset", "medium", "-c:a", "aac", "-b:a", "192k"],
            27: ["-i", str(input_path), "-c:v", "libx264", "-crf", "30",
                 "-c:a", "aac", "-b:a", "96k"],
            28: ["-i", str(input_path), "-c:v", "libx265", "-crf", "28",
                 "-c:a", "aac", "-b:a", "128k"],
            29: ["-i", str(input_path), "-c:v", "libx265", "-crf", "32",
                 "-c:a", "aac", "-b:a", "96k"],
            30: ["-i", str(input_path), "-b:v", "1500k",
                 "-c:a", "aac", "-b:a", "128k"],
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        cmd_args = cmd_map[operation_id]
        output_path = params.get("output_path") or self._build_output_path(input_path, "_compressed", ".mp4")
        cmd_args.append(str(output_path))

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Compressing")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            # Show file size comparison
            input_size = input_path.stat().st_size
            output_size = output_path.stat().st_size
            ratio = (1 - output_size / input_size) * 100 if input_size > 0 else 0
            size_msg = f"Size reduced by {ratio:.1f}% ({input_size // 1048576}MB → {output_size // 1048576}MB)"

            return OperationResult(
                True,
                f"Compressed → {output_path.name} | {size_msg} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        else:
            progress.error()
            return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
