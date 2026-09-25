"""
operations/combos.py - Smart combination operations ("Power Tools").
Multi-step composite workflows:
  99: Reels/Shorts/TikTok vertical video maker
 100: Discord/WhatsApp target-size compressor
 101: 2-Pass High-Quality GIF maker
 102: One-pass multi-effect pipeline
"""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult
from ffram.core.runner import run_ffmpeg, run_two_pass
from ffram.core.probe import probe
from ffram.ui.progress_bar import FFmpegProgressBar
from ffram.ui.console import print_command, format_elapsed, console


class ComboOps(BaseOperation):

    def get_operations(self) -> list[OperationInfo]:
        return [
            OperationInfo(99, "[101] Reels/Shorts Maker (16:9 to 9:16 with Blurred Background)",
                          "Convert landscape to vertical with blurred background",
                          "Smart Combos"),
            OperationInfo(100, "[102] Target Size Compressor (10/25/50 MB for Discord/WhatsApp)",
                          "Compress to exact file size (Discord 10/25/50 MB, WhatsApp 16 MB, or custom)",
                          "Smart Combos"),
            OperationInfo(101, "[103] High-Quality 2-Pass GIF Creation (Palettegen + Paletteuse)",
                          "Create beautiful GIF with optimal palette (palettegen + paletteuse)",
                          "Smart Combos"),
            OperationInfo(102, "[104] Multi-Effect Pipeline (Trim + Resize + Watermark + Loudnorm)",
                          "Combine Trim + Resize + Watermark + Loudnorm in one pass",
                          "Smart Combos"),
        ]

    def execute(self, operation_id: int, params: dict) -> OperationResult:
        if operation_id == 99:
            return self._reels_maker(params)
        elif operation_id == 100:
            return self._target_size(params)
        elif operation_id == 101:
            return self._hq_gif(params)
        elif operation_id == 102:
            return self._multi_effect(params)
        return OperationResult(False, f"Unknown combo operation: {operation_id}")

    def _reels_maker(self, params: dict) -> OperationResult:
        """
        Convert 16:9 landscape to 9:16 vertical with blurred background.
        Creates a 1080x1920 video with:
        - Background: blurred + scaled original filling 1080x1920
        - Foreground: original video centered with correct aspect ratio
        """
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_reels", ".mp4")

        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:5[bg];"
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
        )

        cmd_args = [
            "-i", str(input_path),
            "-filter_complex", filter_complex,
            "-map", "[v]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "23", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ]

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Creating Reels/Shorts")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Reels created (1080×1920) → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        progress.error()
        return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

    def _target_size(self, params: dict) -> OperationResult:
        """
        Compress video to hit a target file size using 2-pass encoding.
        Calculates exact bitrate: target_bits / duration - audio_bitrate
        """
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        target_mb = params.get("target_size_mb", 25)
        output_path = params.get("output_path") or self._build_output_path(
            input_path, f"_{target_mb}mb", ".mp4"
        )

        if duration <= 0:
            try:
                info = probe(input_path)
                duration = info.duration
            except Exception:
                return OperationResult(False, "Cannot determine video duration for target size calculation.")

        audio_bitrate = 128  # kbps
        target_bits = target_mb * 8 * 1024  # kilobits
        video_bitrate = int((target_bits / duration) - audio_bitrate)

        if video_bitrate <= 50:
            return OperationResult(
                False,
                f"Target size {target_mb}MB is too small for a {duration:.0f}s video. "
                f"Minimum required: ~{int((50 + audio_bitrate) * duration / 8 / 1024)}MB"
            )

        console.print(f"  [info]Calculated video bitrate: {video_bitrate}k for {target_mb}MB target[/info]")

        # Pass 1: Analysis
        pass1_cmd = [
            "-i", str(input_path),
            "-c:v", "libx264", "-b:v", f"{video_bitrate}k",
            "-pass", "1", "-passlogfile", str(input_path.parent / "ffmpeg2pass"),
            "-an", "-f", "null", "NUL",
        ]

        # Pass 2: Encode
        pass2_cmd = [
            "-i", str(input_path),
            "-c:v", "libx264", "-b:v", f"{video_bitrate}k",
            "-pass", "2", "-passlogfile", str(input_path.parent / "ffmpeg2pass"),
            "-c:a", "aac", "-b:a", f"{audio_bitrate}k",
            "-movflags", "+faststart",
            str(output_path),
        ]

        print_command(["ffmpeg", "-y"] + pass1_cmd)

        progress = FFmpegProgressBar(description=f"Targeting {target_mb}MB (2-pass)")
        progress.start()

        result = run_two_pass(
            pass1_cmd, pass2_cmd,
            duration=duration,
            on_progress=progress.update,
        )

        # Clean up pass log files
        for ext in [".log", "-0.log", "-0.log.mbtree"]:
            log_file = input_path.parent / f"ffmpeg2pass{ext}"
            try:
                log_file.unlink()
            except OSError:
                pass

        if result.success:
            progress.finish()
            actual_size = output_path.stat().st_size / (1024 * 1024)
            return OperationResult(
                True,
                f"Compressed to {actual_size:.1f}MB (target: {target_mb}MB) → {output_path.name} "
                f"({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        progress.error()
        return OperationResult(False, f"Failed: {result.error_message}", command=result.command)

    def _hq_gif(self, params: dict) -> OperationResult:
        """
        Create high-quality GIF using 2-pass palettegen + paletteuse.
        Produces much better color reproduction than single-pass GIF.
        """
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        fps = params.get("gif_fps", 15)
        width = params.get("gif_width", 640)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_hq", ".gif")
        palette_path = input_path.parent / "_palette.png"

        # Pass 1: Generate palette
        pass1_cmd = [
            "-i", str(input_path),
            "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,palettegen=stats_mode=diff",
            str(palette_path),
        ]

        # Pass 2: Use palette
        pass2_cmd = [
            "-i", str(input_path), "-i", str(palette_path),
            "-filter_complex",
            f"[0:v]fps={fps},scale={width}:-1:flags=lanczos[x];[x][1:v]paletteuse=dither=floyd_steinberg",
            str(output_path),
        ]

        console.print(f"  [info]🎨 Creating HQ GIF: {fps}fps, {width}px wide, Floyd-Steinberg dithering[/info]")

        progress = FFmpegProgressBar(description="Creating HQ GIF (2-pass)")
        progress.start()

        # Run pass 1
        result1 = run_ffmpeg(pass1_cmd, duration=duration)
        if not result1.success:
            progress.error()
            return OperationResult(False, f"Palette generation failed: {result1.error_message}")

        # Run pass 2
        result2 = run_ffmpeg(pass2_cmd, duration=duration, on_progress=progress.update)

        # Clean up palette
        try:
            palette_path.unlink()
        except OSError:
            pass

        total_time = result1.elapsed_seconds + result2.elapsed_seconds

        if result2.success:
            progress.finish()
            size_kb = output_path.stat().st_size / 1024
            return OperationResult(
                True,
                f"HQ GIF created ({size_kb:.0f}KB) → {output_path.name} ({format_elapsed(total_time)})",
                output_path, total_time, result2.command,
            )
        progress.error()
        return OperationResult(False, f"Failed: {result2.error_message}", command=result2.command)

    def _multi_effect(self, params: dict) -> OperationResult:
        """
        One-pass multi-effect pipeline combining:
        - Optional trim (start/end)
        - Optional resize
        - Optional text watermark
        - Audio loudnorm normalization
        """
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_polished", ".mp4")

        # Build command parts
        cmd_args = []
        video_filters = []
        audio_filters = []

        # Trim
        start = params.get("trim_start")
        end = params.get("trim_end")
        if start:
            cmd_args.extend(["-ss", start])
        cmd_args.extend(["-i", str(input_path)])
        if end:
            cmd_args.extend(["-to", end])

        # Video filters
        target_height = params.get("resize_height")
        if target_height:
            video_filters.append(f"scale=-2:{target_height}")

        watermark_text = params.get("watermark_text")
        if watermark_text:
            video_filters.append(
                f"drawtext=text='{watermark_text}':x=20:y=20:fontsize=28:fontcolor=white:shadowx=2:shadowy=2"
            )

        # Audio filters
        if params.get("normalize_audio", True):
            audio_filters.append("loudnorm")

        # Build final command
        if video_filters:
            cmd_args.extend(["-vf", ",".join(video_filters)])
        if audio_filters:
            cmd_args.extend(["-af", ",".join(audio_filters)])

        cmd_args.extend([
            "-c:v", "libx264", "-crf", params.get("crf", "23"),
            "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(output_path),
        ])

        print_command(["ffmpeg", "-y"] + cmd_args)

        progress = FFmpegProgressBar(description="Multi-effect processing")
        progress.start()

        result = run_ffmpeg(cmd_args, duration=duration, on_progress=progress.update)

        if result.success:
            progress.finish()
            return OperationResult(
                True,
                f"Multi-effect complete → {output_path.name} ({format_elapsed(result.elapsed_seconds)})",
                output_path, result.elapsed_seconds, result.command,
            )
        progress.error()
        return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
