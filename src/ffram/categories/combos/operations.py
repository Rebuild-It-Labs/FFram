"""Smart combo operations for multi-step workflows."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg, run_two_pass
from ffram.core.probe import probe
from ffram.ui.console import format_elapsed, console


class ComboOps(BaseOperation):

    def get_operations(self):
        S = "Smart Combos"
        return [
            OperationInfo(99, "Reels/Shorts Maker", "16:9 to 9:16 with blurred background", S),
            OperationInfo(100, "Target Size Compressor", "2-pass encode to exact file size (MB)", S),
            OperationInfo(101, "High-Quality GIF (2-Pass)", "Palettegen + paletteuse for best colors", S),
            OperationInfo(102, "Multi-Effect Pipeline", "Trim + resize + watermark + loudnorm", S),
        ]

    def execute(self, operation_id, params):
        dispatch = {99: self._reels, 100: self._target_size, 101: self._hq_gif, 102: self._multi_effect}
        fn = dispatch.get(operation_id)
        if not fn:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")
        return fn(params)

    def _reels(self, params):
        input_path = Path(params["input_path"])
        output_path = params.get("output_path") or self._build_output_path(input_path, "_reels", ".mp4")

        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:5[bg];"
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
        )
        cmd_args = [
            "-i", str(input_path), "-filter_complex", vf,
            "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "23", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
            str(output_path),
        ]
        return self.run_op(cmd_args, output_path, params.get("duration", 0), "Creating Reels/Shorts")

    def _target_size(self, params):
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        target_mb = params.get("target_size_mb", 25)
        output_path = params.get("output_path") or self._build_output_path(input_path, f"_{target_mb}mb", ".mp4")

        if duration <= 0:
            try:
                duration = probe(input_path).duration
            except Exception:
                return OperationResult(False, "Cannot determine duration for size calculation.")

        audio_br = 128
        video_br = int((target_mb * 8 * 1024 / duration) - audio_br)
        if video_br <= 50:
            return OperationResult(False, f"Target {target_mb}MB too small for {duration:.0f}s video.")

        console.print(f"  Video bitrate: {video_br}k for {target_mb}MB target")
        log = str(input_path.parent / "ffmpeg2pass")

        from ffram.ui.progress_bar import FFmpegProgressBar
        from ffram.ui.console import print_command
        pass1 = ["-i", str(input_path), "-c:v", "libx264", "-b:v", f"{video_br}k", "-pass", "1", "-passlogfile", log, "-an", "-f", "null", "NUL"]
        pass2 = ["-i", str(input_path), "-c:v", "libx264", "-b:v", f"{video_br}k", "-pass", "2", "-passlogfile", log, "-c:a", "aac", "-b:a", f"{audio_br}k", "-movflags", "+faststart", str(output_path)]

        print_command(["ffmpeg", "-y"] + pass1)
        progress = FFmpegProgressBar(description=f"Target {target_mb}MB (2-pass)")
        progress.start()
        result = run_two_pass(pass1, pass2, duration=duration, on_progress=progress.update)

        for ext in [".log", "-0.log", "-0.log.mbtree"]:
            try:
                (input_path.parent / f"ffmpeg2pass{ext}").unlink()
            except OSError:
                pass

        if result.success:
            progress.finish()
            actual = output_path.stat().st_size / (1024 * 1024)
            return OperationResult(True, f"{actual:.1f}MB (target: {target_mb}MB) {output_path.name} ({format_elapsed(result.elapsed_seconds)})", output_path, result.elapsed_seconds, result.command)
        progress.error()
        return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

    def _hq_gif(self, params):
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        fps = params.get("gif_fps", 15)
        width = params.get("gif_width", 640)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_hq", ".gif")
        palette = input_path.parent / "_palette.png"

        pass1 = ["-i", str(input_path), "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,palettegen=stats_mode=diff", str(palette)]
        pass2 = ["-i", str(input_path), "-i", str(palette), "-filter_complex", f"[0:v]fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=floyd_steinberg", str(output_path)]

        console.print(f"  HQ GIF: {fps}fps, {width}px, Floyd-Steinberg dither")

        from ffram.ui.progress_bar import FFmpegProgressBar
        progress = FFmpegProgressBar(description="HQ GIF (2-pass)")
        progress.start()

        r1 = run_ffmpeg(pass1, duration=duration)
        if not r1.success:
            progress.error()
            return OperationResult(False, f"Palette generation failed: {r1.error_message}")

        r2 = run_ffmpeg(pass2, duration=duration, on_progress=progress.update)
        try:
            palette.unlink()
        except OSError:
            pass

        total = r1.elapsed_seconds + r2.elapsed_seconds
        if r2.success:
            progress.finish()
            kb = output_path.stat().st_size / 1024
            return OperationResult(True, f"HQ GIF ({kb:.0f}KB) {output_path.name} ({format_elapsed(total)})", output_path, total, r2.command)
        progress.error()
        return OperationResult(False, f"Failed: {r2.error_message}", command=r2.command)

    def _multi_effect(self, params):
        input_path = Path(params["input_path"])
        output_path = params.get("output_path") or self._build_output_path(input_path, "_polished", ".mp4")

        cmd = []
        vf, af = [], []

        start = params.get("trim_start")
        if start:
            cmd.extend(["-ss", start])
        cmd.extend(["-i", str(input_path)])
        end = params.get("trim_end")
        if end:
            cmd.extend(["-to", end])

        h = params.get("resize_height")
        if h:
            vf.append(f"scale=-2:{h}")
        text = params.get("watermark_text")
        if text:
            vf.append(f"drawtext=text='{text}':x=20:y=20:fontsize=28:fontcolor=white:shadowx=2:shadowy=2")
        if params.get("normalize_audio", True):
            af.append("loudnorm")

        if vf:
            cmd.extend(["-vf", ",".join(vf)])
        if af:
            cmd.extend(["-af", ",".join(af)])

        cmd.extend(["-c:v", "libx264", "-crf", params.get("crf", "23"), "-preset", "medium",
                     "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(output_path)])
        return self.run_op(cmd, output_path, params.get("duration", 0), "Multi-effect pipeline")
