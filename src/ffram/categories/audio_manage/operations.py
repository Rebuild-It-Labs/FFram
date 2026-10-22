"""Audio track management operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class AudioManageOps(BaseOperation):

    def get_operations(self):
        A = "Audio Management"
        ai = {"needs_second_input": True, "second_input_label": "Audio File", "second_input_types": ["audio"]}
        vi = {"needs_second_input": True, "second_input_label": "Source Video (with audio tracks)", "second_input_types": ["video", "audio"]}
        return [
            OperationInfo(9, "Add Audio to Silent Video", "Mux audio into video with no audio", A, **ai),
            OperationInfo(10, "Add Second Audio Track", "Keep original, add extra audio stream", A, **ai),
            OperationInfo(11, "Replace Audio Track", "Swap existing audio with new file", A, **ai),
            OperationInfo(12, "Add Audio (Keep Original)", "Add track alongside original audio", A, **ai),
            OperationInfo(13, "Add Audio (Loop to Fit)", "Loop short audio to match video length", A, **ai),
            OperationInfo(14, "Mix Background Music", "Blend music with original audio", A, **ai),
            OperationInfo(15, "Mix Background Music (20%)", "Background music at 20% volume", A, **ai),
            OperationInfo(16, "Replace Audio (Match Length)", "Replace audio, trim video to audio length", A, **ai),
            OperationInfo(103, "Transfer Audio Track (Lossless Remux)", "Select 1 audio from multi-track video & inject into 2nd video (lossless)", A, **vi),
        ]

    def execute(self, operation_id, params):
        if operation_id == 103:
            return self._execute_track_transfer(params)

        i = str(Path(params["input_path"]))
        a = str(Path(params["second_input_path"]))
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_audio_edit", ".mp4")
        o = str(output_path)

        cmd_map = {
            9:  ["-i", i, "-i", a, "-c:v", "copy", "-c:a", "aac", "-shortest", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
            10: ["-i", i, "-i", a, "-map", "0:v", "-map", "0:a?", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
            11: ["-i", i, "-i", a, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
            12: ["-i", i, "-i", a, "-map", "0:v", "-map", "0:a?", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
            13: ["-stream_loop", "-1", "-i", a, "-i", i, "-map", "1:v", "-map", "0:a", "-c:v", "copy", "-c:a", "aac", "-shortest", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
            14: ["-i", i, "-i", a, "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first", "-c:v", "copy", "-c:a", "aac", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
            15: ["-i", i, "-i", a, "-filter_complex", "[1:a]volume=0.2[m];[0:a][m]amix=inputs=2:duration=first", "-c:v", "copy", "-c:a", "aac", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
            16: ["-i", i, "-i", a, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", "-max_interleave_delta", "0", "-max_muxing_queue_size", "2048", "-movflags", "+faststart", o],
        }

        if operation_id not in cmd_map:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        return self.run_op(cmd_map[operation_id], output_path, duration, "Processing audio")

    def _execute_track_transfer(self, params):
        from ffram.core.probe import probe
        target_path = Path(params["input_path"])
        source_path = Path(params["second_input_path"])

        try:
            target_info = probe(target_path)
            source_info = probe(source_path)
        except Exception as e:
            return OperationResult(False, f"Failed to probe media files: {e}")

        source_audio_tracks = source_info.audio_streams
        if not source_audio_tracks:
            return OperationResult(False, f"No audio tracks found in source file: {source_path.name}")

        source_idx = int(params.get("source_audio_index", 0))
        if source_idx < 0 or source_idx >= len(source_audio_tracks):
            source_idx = 0
        selected_track = source_audio_tracks[source_idx]

        target_audio_tracks = target_info.audio_streams
        placement_mode = params.get("placement_mode", "only_new" if not target_audio_tracks else "add_secondary")

        output_ext = params.get("output_container")
        if not output_ext:
            output_ext = target_path.suffix

        # Lossless compatibility check
        incompatible_mp4_codecs = {"flac", "pcm_s16le", "pcm_s24le", "pcm_s32le", "dts", "truehd", "vorbis"}
        if output_ext.lower() == ".mp4" and selected_track.codec_name.lower() in incompatible_mp4_codecs and not params.get("transcode_audio", False):
            if not params.get("force_mp4", False):
                output_ext = ".mkv"

        suffix = f"_{placement_mode}"
        output_path = params.get("output_path") or self._build_output_path(target_path, suffix, output_ext)

        cmd = [
            "-i", str(target_path),
            "-i", str(source_path),
            "-map", "0:v:0",
        ]

        new_track_lang = params.get("new_track_lang")
        new_track_title = params.get("new_track_title")

        if placement_mode == "only_new":
            cmd.extend(["-map", f"1:a:{source_idx}"])
            cmd.extend(["-disposition:a:0", "default"])
            out_idx = 0
            if new_track_lang:
                cmd.extend([f"-metadata:s:a:{out_idx}", f"language={new_track_lang}"])
            if new_track_title:
                cmd.extend([f"-metadata:s:a:{out_idx}", f"title={new_track_title}"])

        elif placement_mode == "make_primary":
            cmd.extend([f"-map", f"1:a:{source_idx}"])
            if target_audio_tracks:
                cmd.extend(["-map", "0:a"])
            cmd.extend(["-disposition:a:0", "default"])
            if target_audio_tracks:
                for i in range(1, len(target_audio_tracks) + 1):
                    cmd.extend([f"-disposition:a:{i}", "0"])
            out_idx = 0
            if new_track_lang:
                cmd.extend([f"-metadata:s:a:{out_idx}", f"language={new_track_lang}"])
            if new_track_title:
                cmd.extend([f"-metadata:s:a:{out_idx}", f"title={new_track_title}"])

        elif placement_mode == "replace_specific":
            replace_idx = int(params.get("target_replace_index", 0))
            num_target_tracks = len(target_audio_tracks)
            for i in range(num_target_tracks):
                if i == replace_idx:
                    cmd.extend(["-map", f"1:a:{source_idx}"])
                    if new_track_lang:
                        cmd.extend([f"-metadata:s:a:{i}", f"language={new_track_lang}"])
                    if new_track_title:
                        cmd.extend([f"-metadata:s:a:{i}", f"title={new_track_title}"])
                else:
                    cmd.extend(["-map", f"0:a:{i}"])

        else:  # "add_secondary" / "keep_both"
            if target_audio_tracks:
                cmd.extend(["-map", "0:a"])
            cmd.extend(["-map", f"1:a:{source_idx}"])
            out_idx = len(target_audio_tracks)
            if not target_audio_tracks:
                cmd.extend(["-disposition:a:0", "default"])
            else:
                cmd.extend([f"-disposition:a:{out_idx}", "0"])
            if new_track_lang:
                cmd.extend([f"-metadata:s:a:{out_idx}", f"language={new_track_lang}"])
            if new_track_title:
                cmd.extend([f"-metadata:s:a:{out_idx}", f"title={new_track_title}"])

        # Preserve subtitles and global metadata
        if params.get("include_subtitles", True):
            cmd.extend(["-map", "0:s?"])

        cmd.extend(["-map_metadata", "0"])

        # Codecs: 100% lossless stream copy by default
        cmd.extend(["-c:v", "copy"])
        if params.get("transcode_audio", False):
            cmd.extend(["-c:a", "aac", "-b:a", "320k"])
        else:
            cmd.extend(["-c:a", "copy"])
        cmd.extend(["-c:s", "copy"])

        # CRITICAL: Ensure perfect frame-by-frame interleaving across multiple input files.
        # Without -max_interleave_delta 0, sparse streams (like forced subtitles or multi-tracks)
        # cause FFmpeg to stop interleaving and flush audio in giant multi-gigabyte lumps at the
        # end of the file, making media players freeze or fail to play.
        cmd.extend(["-max_interleave_delta", "0", "-max_muxing_queue_size", "2048"])

        if params.get("duration_mode") == "shortest":
            cmd.append("-shortest")

        cmd.append(str(output_path))

        desc = "Transferring audio track (Lossless)"
        duration = target_info.duration or params.get("duration", 0)
        return self.run_op(cmd, output_path, duration, desc)
