"""Batch processing operations for folders of media files."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg
from ffram.core.probe import probe
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import console, print_error, format_elapsed


class BatchOps(BaseOperation):

    def get_operations(self):
        B = "Batch Processing"
        return [
            OperationInfo(94, "Batch MP4 to MP3", "Convert every MP4 in folder to MP3", B),
            OperationInfo(95, "Batch Resize to 720p", "Resize every MP4 in folder", B),
            OperationInfo(96, "Batch Compress (CRF 28)", "Compress every MP4 in folder", B),
            OperationInfo(97, "Batch Extract Audio", "Extract audio from every MP4 (stream copy)", B),
            OperationInfo(98, "Batch Add Audio", "Add same audio to every MP4", B,
                          needs_second_input=True, second_input_label="Audio File", second_input_types=["audio"]),
        ]

    def _get_mp4_files(self, directory):
        return sorted([f for f in directory.glob("*.mp4") if f.is_file()])

    def _build_cmd(self, op_id, file, params):
        """Return (cmd_args, output_path) for a single file."""
        f = str(file)
        s = file.stem
        d = file.parent
        if op_id == 94:
            return ["-i", f, "-vn", "-c:a", "libmp3lame", "-q:a", "2"], d / f"{s}.mp3"
        if op_id == 95:
            return ["-i", f, "-vf", "scale=-2:720", "-c:v", "libx264", "-crf", "23", "-c:a", "aac"], d / f"{s}_720p.mp4"
        if op_id == 96:
            return ["-i", f, "-c:v", "libx264", "-crf", "28", "-c:a", "aac", "-b:a", "128k"], d / f"{s}_compressed.mp4"
        if op_id == 97:
            return ["-i", f, "-vn", "-c:a", "copy"], d / f"{s}.m4a"
        if op_id == 98:
            a = str(Path(params["second_input_path"]))
            return ["-i", f, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest"], d / f"{s}_new.mp4"
        return None, None

    def execute(self, operation_id, params):
        input_dir = Path(params.get("input_dir", params.get("input_path", ""))).parent
        if "input_dir" in params:
            input_dir = Path(params["input_dir"])

        files = self._get_mp4_files(input_dir)
        if not files:
            return OperationResult(False, f"No MP4 files found in {input_dir}")

        total = len(files)
        ok, fail, elapsed = 0, 0, 0.0
        console.print(f"\n  Found {total} MP4 files in {input_dir}\n")

        for idx, file in enumerate(files, 1):
            console.print(f"  [{idx}/{total}] {file.name}")
            try:
                dur = probe(file).duration
            except Exception:
                dur = 0

            cmd, out = self._build_cmd(operation_id, file, params)
            if cmd is None:
                return OperationResult(False, f"Unknown operation ID: {operation_id}")

            cmd.append(str(out))
            progress = FFmpegProgressBar(description=f"[{idx}/{total}] {file.stem}")
            progress.start()
            result = run_ffmpeg(cmd, duration=dur, on_progress=progress.update)

            if result.success:
                progress.finish(); ok += 1
            else:
                progress.error(); fail += 1
                print_error(f"  Failed: {file.name} - {result.error_message}")
            elapsed += result.elapsed_seconds

        msg = f"Batch: {ok}/{total} succeeded"
        if fail:
            msg += f", {fail} failed"
        msg += f" ({format_elapsed(elapsed)})"
        return OperationResult(success=fail == 0, message=msg, elapsed_seconds=elapsed)
