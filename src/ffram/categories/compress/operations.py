"""Video compression operations."""

from pathlib import Path
from ffram.categories.base import BaseOperation, OperationInfo, OperationResult


class CompressOps(BaseOperation):

    def get_operations(self):
        C = "Compress Video"
        return [
            OperationInfo(200, "Smart Auto-CRF (VMAF AI)", "Find optimal CRF for 95 VMAF and encode", C),
            OperationInfo(201, "Distributed Cluster Encode", "Split and encode video across multiple nodes", C),
            OperationInfo(25, "Compress H.264 (CRF 28)", "Good balance of quality and size", C),
            OperationInfo(26, "Compress H.264 (CRF 20)", "Near-lossless visual quality", C),
            OperationInfo(27, "Compress H.264 (CRF 30)", "Smaller file, lower quality", C),
            OperationInfo(28, "Compress H.265 (CRF 28)", "50% smaller than H.264 at same quality", C),
            OperationInfo(29, "Compress H.265 (CRF 32)", "Maximum H.265 compression", C),
            OperationInfo(30, "Target Bitrate (1500 kbps)", "Compress to specific bitrate", C),
        ]

    def execute(self, operation_id, params):
        i = str(Path(params["input_path"]))

        if operation_id == 200:
            from ffram.core.vmaf import suggest_optimal_crf
            from ffram.ui.console import console
            console.print("  [dim]Running VMAF analysis...[/dim]")
            def update_progress(msg):
                console.print(f"  [dim]- {msg}[/dim]")
            best_crf = suggest_optimal_crf(i, target_vmaf=95.0, on_progress=update_progress)
            console.print(f"  [bold green]Optimal CRF found: {best_crf}[/bold green]")
            
            cmd = ["-i", i, "-c:v", "libx264", "-crf", str(best_crf), "-preset", "slow", "-c:a", "aac", "-b:a", "128k"]
            output_path = self._build_output_path(Path(i), "_auto_crf", ".mp4")
            cmd.append(str(output_path))
            return self.run_op(cmd, output_path, params.get("duration", 0), "Encoding with optimal CRF")

        elif operation_id == 201:
            from ffram.core.cluster import MasterNode
            from ffram.ui.console import console
            workers = params.get("workers", ["http://localhost:8000"])
            
            cmd_template = ["-i", "{input}", "-c:v", "libx264", "-crf", "23", "-preset", "medium", "-c:a", "aac", "-y", "{output}"]
            output_path = self._build_output_path(Path(i), "_cluster", ".mp4")
            
            console.print(f"  [dim]Starting distributed encode on {len(workers)} workers...[/dim]")
            master = MasterNode(worker_urls=workers)
            success = master.process_video(i, output_path, cmd_template)
            
            if success:
                return OperationResult(True, "Cluster encode complete", output_path)
            else:
                return OperationResult(False, "Cluster encode failed")

        cmd_map = {
            25: (["-i", i, "-c:v", "libx264", "-crf", "28", "-c:a", "aac", "-b:a", "128k"], "_compressed", ".mp4"),
            26: (["-i", i, "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-c:a", "aac", "-b:a", "192k"], "_compressed", ".mp4"),
            27: (["-i", i, "-c:v", "libx264", "-crf", "30", "-c:a", "aac", "-b:a", "96k"], "_compressed", ".mp4"),
            28: (["-i", i, "-c:v", "libx265", "-crf", "28", "-c:a", "aac", "-b:a", "128k"], "_compressed", ".mp4"),
            29: (["-i", i, "-c:v", "libx265", "-crf", "32", "-c:a", "aac", "-b:a", "96k"], "_compressed", ".mp4"),
            30: (["-i", i, "-b:v", "1500k", "-c:a", "aac", "-b:a", "128k"], "_compressed", ".mp4"),
        }
        return self.run_map(operation_id, params, cmd_map, "Compressing")
