"""Video concatenation and joining operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult

VMULTI = {"needs_second_input": True, "second_input_label": "Video Files to Join", "second_input_types": ["video_multi"]}
VSINGLE = {"needs_second_input": True, "second_input_label": "Second Video", "second_input_types": ["video"]}


class ConcatOps(BaseOperation):

    def get_operations(self):
        C = "Combine Videos"
        return [
            OperationInfo(73, "Concat (Same Codec)", "Lossless concat via demuxer", C, **VMULTI),
            OperationInfo(74, "Concat (Re-encode)", "Join different codecs with re-encoding", C, **VMULTI),
            OperationInfo(75, "Join Two Videos", "Concat two videos using filter_complex", C, **VSINGLE),
            OperationInfo(104, "Top-Bottom Collage Comparison", "Stack 2 videos vertically with filename labels for visual comparison", C,
                          needs_second_input=True, second_input_label="Bottom Video (Comparison)", second_input_types=["video"]),
        ]

    def _write_concat_list(self, input_path, file_list):
        """Write a temp concat list file and return its path."""
        list_file = input_path.parent / "_concat_list.txt"
        files = [Path(f) if isinstance(f, str) else f for f in file_list]
        with open(list_file, "w", encoding="utf-8") as fh:
            for f in files:
                escaped = str(f).replace("\\", "/").replace("'", "'\\''")
                fh.write(f"file '{escaped}'\n")
        return list_file, files

    def execute(self, operation_id, params):
        if operation_id == 104:
            return self._execute_collage_comparison(params)

        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        if operation_id in (73, 74):
            list_file, files = self._write_concat_list(input_path, params.get("file_list", [input_path]))
            output_path = params.get("output_path") or self._build_output_path(input_path, "_merged", ".mp4")
            codec = (
                ["-c", "copy", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart"]
                if operation_id == 73
                else ["-c:v", "libx264", "-c:a", "aac", "-movflags", "+faststart"]
            )
            cmd_args = ["-f", "concat", "-safe", "0", "-i", str(list_file)] + codec + [str(output_path)]
            result = self.run_op(cmd_args, output_path, duration, "Merging videos")
            try:
                list_file.unlink()
            except OSError:
                pass
            return result

        if operation_id == 75:
            second = str(Path(params["second_input_path"]))
            output_path = params.get("output_path") or self._build_output_path(input_path, "_joined", ".mp4")
            cmd_args = [
                "-i", str(input_path), "-i", second,
                "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]",
                "-map", "[v]", "-map", "[a]",
                "-movflags", "+faststart",
                str(output_path),
            ]
            return self.run_op(cmd_args, output_path, duration, "Joining videos")

        return OperationResult(False, f"Unknown operation ID: {operation_id}")

    def _execute_collage_comparison(self, params):
        from ffram.core.probe import probe
        top_path = Path(params["input_path"])
        bottom_path = Path(params["second_input_path"])

        try:
            top_info = probe(top_path)
            bot_info = probe(bottom_path)
        except Exception as e:
            return OperationResult(False, f"Failed to probe comparison videos: {e}")

        # Determine target width
        w0 = top_info.width or 1280
        w1 = bot_info.width or 1280
        width_mode = params.get("target_width", "max")
        if width_mode == "1080p":
            target_w = 1920
        elif width_mode == "720p":
            target_w = 1280
        elif width_mode == "video1":
            target_w = w0
        else:
            target_w = max(w0, w1)

        # Make sure width is even for libx264
        if target_w % 2 != 0:
            target_w += 1

        # Labels
        label_top = params.get("top_label") or f"Top: {top_path.name}"
        label_bot = params.get("bottom_label") or f"Bottom: {bottom_path.name}"

        # Escape for FFmpeg drawtext
        esc_top = label_top.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")
        esc_bot = label_bot.replace("\\", "\\\\").replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")

        fontsize = max(18, min(42, int(target_w / 40)))
        pos = params.get("label_position", "top_left")
        if pos == "top_center":
            pos_x = "(w-text_w)/2"
            pos_y = "20"
        else:
            pos_x = "24"
            pos_y = "20"

        font_color = params.get("font_color", "white")
        box_color = params.get("box_color", "black@0.7")

        divider = params.get("divider_line", True)
        div_h = 4 if divider else 0
        div_color = params.get("divider_color", "yellow")

        # Build filtergraph
        top_filter = f"[0:v]scale={target_w}:-2:flags=lanczos,drawtext=text='{esc_top}':x={pos_x}:y={pos_y}:fontsize={fontsize}:fontcolor={font_color}:box=1:boxcolor={box_color}:boxborderw=8"
        if div_h > 0:
            top_filter += f",pad={target_w}:ih+{div_h}:0:0:color={div_color}"
        top_filter += "[top];"

        bot_filter = f"[1:v]scale={target_w}:-2:flags=lanczos,drawtext=text='{esc_bot}':x={pos_x}:y={pos_y}:fontsize={fontsize}:fontcolor={font_color}:box=1:boxcolor={box_color}:boxborderw=8[bot];"
        stack_filter = "[top][bot]vstack=inputs=2[v]"

        filter_complex = top_filter + bot_filter + stack_filter

        output_path = params.get("output_path") or self._build_output_path(top_path, "_collage_compare", ".mp4")

        cmd = [
            "-i", str(top_path),
            "-i", str(bottom_path),
        ]

        # Audio handling
        audio_mode = params.get("audio_source", "top")
        has_a0 = top_info.has_audio
        has_a1 = bot_info.has_audio

        if audio_mode == "mute" or (not has_a0 and not has_a1):
            cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-an"])
        elif audio_mode == "bottom" and has_a1:
            cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"])
        elif audio_mode == "mix" and has_a0 and has_a1:
            filter_complex += ";[0:a][1:a]amix=inputs=2:duration=first[a]"
            cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "[a]", "-c:a", "aac", "-b:a", "192k"])
        else:
            if has_a0:
                cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "0:a:0", "-c:a", "aac", "-b:a", "192k"])
            elif has_a1:
                cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-map", "1:a:0", "-c:a", "aac", "-b:a", "192k"])
            else:
                cmd.extend(["-filter_complex", filter_complex, "-map", "[v]", "-an"])

        # High-fidelity video encoding for visual comparison
        crf = str(params.get("crf", "18"))
        preset = params.get("preset", "fast")
        cmd.extend(["-c:v", "libx264", "-crf", crf, "-preset", preset, "-pix_fmt", "yuv420p", "-movflags", "+faststart"])

        # End when either video finishes
        cmd.append("-shortest")
        cmd.append(str(output_path))

        dur0 = top_info.duration or 0
        dur1 = bot_info.duration or 0
        est_duration = min(dur0, dur1) if (dur0 > 0 and dur1 > 0) else (dur0 or dur1 or params.get("duration", 0))

        return self.run_op(cmd, output_path, est_duration, "Creating Top-Bottom Collage")
