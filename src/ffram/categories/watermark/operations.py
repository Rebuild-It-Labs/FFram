"""Watermark and text overlay operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult

IMG = {"needs_second_input": True, "second_input_label": "Watermark Image", "second_input_types": ["image"]}


class WatermarkOps(BaseOperation):

    def get_operations(self):
        W = "Overlay / Watermark"
        return [
            OperationInfo(76, "Image Watermark (Top-Left)", "Overlay logo at top-left", W, **IMG),
            OperationInfo(77, "Image Watermark (Bottom-Right)", "Overlay logo at bottom-right", W, **IMG),
            OperationInfo(78, "Semi-Transparent Watermark", "50% transparent overlay", W, **IMG),
            OperationInfo(79, "Add Text Overlay", "Burn text into video", W),
            OperationInfo(80, "Add Timecode Overlay", "Burn running timecode", W),
        ]

    def execute(self, operation_id, params):
        input_path = Path(params["input_path"])
        i = str(input_path)
        duration = params.get("duration", 0)
        output_path = params.get("output_path") or self._build_output_path(input_path, "_watermarked", ".mp4")
        o = str(output_path)

        if operation_id in (76, 77, 78):
            logo = str(Path(params["second_input_path"]))
            filters = {
                76: "overlay=10:10",
                77: "overlay=W-w-10:H-h-10",
                78: "[1:v]format=rgba,colorchannelmixer=aa=0.5[logo];[0:v][logo]overlay=10:10",
            }
            cmd_args = ["-i", i, "-i", logo, "-filter_complex", filters[operation_id], o]
        elif operation_id == 79:
            text = params.get("text", "My Video")
            size = params.get("font_size", "40")
            color = params.get("font_color", "white")
            cmd_args = ["-i", i, "-vf", f"drawtext=text='{text}':x=50:y=50:fontsize={size}:fontcolor={color}", o]
        elif operation_id == 80:
            cmd_args = ["-i", i, "-vf", "drawtext=text='%{pts\\:hms}':x=20:y=20:fontsize=30:fontcolor=white", o]
        else:
            return OperationResult(False, f"Unknown operation ID: {operation_id}")

        return self.run_op(cmd_args, output_path, duration, "Adding overlay")
