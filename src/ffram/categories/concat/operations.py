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
        input_path = Path(params["input_path"])
        duration = params.get("duration", 0)

        if operation_id in (73, 74):
            list_file, files = self._write_concat_list(input_path, params.get("file_list", [input_path]))
            output_path = params.get("output_path") or self._build_output_path(input_path, "_merged", ".mp4")
            codec = ["-c", "copy"] if operation_id == 73 else ["-c:v", "libx264", "-c:a", "aac"]
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
                "-map", "[v]", "-map", "[a]", str(output_path),
            ]
            return self.run_op(cmd_args, output_path, duration, "Joining videos")

        return OperationResult(False, f"Unknown operation ID: {operation_id}")
