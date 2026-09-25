"""
operations/batch.py - Batch processing operations (Operations 94-98).
Processes all matching files in a directory with per-file and total progress tracking.
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.core.probe import probe
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import console, print_command, print_success, print_error, format_elapsed


class BatchOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(94, "[96] Batch Convert: All MP4 files in folder to MP3", "Convert every MP4 in folder to MP3", "Batch Processing"),
            OperationInfo(95, "[97] Batch Scale: All MP4 files in folder to 720p", "Resize every MP4 in folder to 720p", "Batch Processing"),
            OperationInfo(96, "Batch: Compress all MP4", "Compress every MP4 in folder (CRF 28)", "Batch Processing"),
            OperationInfo(97, "Batch: Extract audio from all", "Extract audio from every MP4 (stream copy)", "Batch Processing"),
            OperationInfo(98, "Batch: Add audio to all videos", "Add same audio to every MP4 in folder",
                          "Batch Processing", needs_second_input=True,
                          second_input_label="Audio File to Add", second_input_types=["audio"]),
        ]

    def _get_mp4_files(self, directory: Path) -> list[Path]:
        """Get all MP4 files in directory, sorted by name."""
        files = sorted(directory.glob("*.mp4"))
        return [f for f in files if f.is_file()]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        input_dir = Path(params.get("input_dir", params.get("input_path", ""))).parent
        if "input_dir" in params:
            input_dir = Path(params["input_dir"])

        files = self._get_mp4_files(input_dir)
        if not files:
            return OperationResult(False, f"No MP4 files found in {input_dir}")

        total = len(files)
        success_count = 0
        fail_count = 0
        total_elapsed = 0.0

        console.print(f"\n  [info]📂 Found {total} MP4 files in {input_dir}[/info]\n")

        for i, file in enumerate(files, 1):
            console.print(f"  [dim]▸ [{i}/{total}] {file.name}[/dim]")

            try:
                info = probe(file)
                duration = info.duration
            except Exception:
                duration = 0

            if operation_id == 94:
                # MP4 → MP3
                output = file.parent / f"{file.stem}.mp3"
                cmd = ["-i", str(file), "-vn", "-c:a", "libmp3lame", "-q:a", "2", str(output)]

            elif operation_id == 95:
                # MP4 → 720p
                output = file.parent / f"{file.stem}_720p.mp4"
                cmd = ["-i", str(file), "-vf", "scale=-2:720",
                       "-c:v", "libx264", "-crf", "23", "-c:a", "aac", str(output)]

            elif operation_id == 96:
                # Compress
                output = file.parent / f"{file.stem}_compressed.mp4"
                cmd = ["-i", str(file), "-c:v", "libx264", "-crf", "28",
                       "-c:a", "aac", "-b:a", "128k", str(output)]

            elif operation_id == 97:
                # Extract audio
                output = file.parent / f"{file.stem}.m4a"
                cmd = ["-i", str(file), "-vn", "-c:a", "copy", str(output)]

            elif operation_id == 98:
                # Add audio
                audio_path = Path(params["second_input_path"])
                output = file.parent / f"{file.stem}_new.mp4"
                cmd = ["-i", str(file), "-i", str(audio_path),
                       "-map", "0:v", "-map", "1:a",
                       "-c:v", "copy", "-c:a", "aac", "-shortest", str(output)]
            else:
                return OperationResult(False, f"Unknown operation ID: {operation_id}")

            progress = FFmpegProgressBar(description=f"[{i}/{total}] {file.stem}")
            progress.start()

            result = run_ffmpeg(cmd, duration=duration, on_progress=progress.update)

            if result.success:
                progress.finish()
                success_count += 1
            else:
                progress.error()
                fail_count += 1
                print_error(f"  Failed: {file.name} - {result.error_message}")

            total_elapsed += result.elapsed_seconds

        msg = f"Batch complete: {success_count}/{total} succeeded"
        if fail_count > 0:
            msg += f", {fail_count} failed"
        msg += f" ({format_elapsed(total_elapsed)})"

        return OperationResult(
            success=fail_count == 0,
            message=msg,
            elapsed_seconds=total_elapsed,
        )
