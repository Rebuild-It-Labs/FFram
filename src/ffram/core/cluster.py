"""
core/cluster.py - Distributed chunk encoding using xmlrpc.
Provides Master and Worker nodes for dividing media into chunks and distributing the workload.
"""

import os
import glob
import time
import socket
import threading
from pathlib import Path
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client

from ffram.core.runner import run_ffmpeg


class WorkerNode:
    def __init__(self, host: str = "0.0.0.0", port: int = 8000, ffmpeg_path: str = "ffmpeg"):
        self.host = host
        self.port = port
        self.ffmpeg_path = ffmpeg_path
        self.server = SimpleXMLRPCServer((self.host, self.port), allow_none=True)
        self.server.register_function(self.process_chunk, "process_chunk")
        self.server.register_function(self.ping, "ping")

    def ping(self) -> str:
        return "pong"

    def process_chunk(self, chunk_data: bytes, ext: str, cmd_template: list[str]) -> dict:
        """
        Receives chunk data, writes it to disk, runs the cmd_template, 
        and returns the encoded data.
        cmd_template should use '{input}' and '{output}'.
        """
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / f"input{ext}"
            output_path = Path(temp_dir) / f"output{ext}"
            
            with open(input_path, "wb") as f:
                f.write(chunk_data.data if hasattr(chunk_data, "data") else chunk_data)

            # Build command
            cmd = []
            for arg in cmd_template:
                cmd.append(arg.replace("{input}", str(input_path)).replace("{output}", str(output_path)))
                
            res = run_ffmpeg(cmd, ffmpeg_path=self.ffmpeg_path)
            
            if res.success and output_path.exists():
                with open(output_path, "rb") as f:
                    out_data = f.read()
                return {"success": True, "data": out_data}
            else:
                return {"success": False, "error": res.error_message}

    def start(self):
        print(f"Worker Node started on {self.host}:{self.port}")
        self.server.serve_forever()


class MasterNode:
    def __init__(self, worker_urls: list[str], ffmpeg_path: str = "ffmpeg"):
        self.worker_urls = worker_urls
        self.ffmpeg_path = ffmpeg_path

    def process_video(self, input_path: str | Path, output_path: str | Path, cmd_template: list[str]) -> bool:
        """
        Splits video into chunks, sends to workers, and concatenates the results.
        cmd_template should use '{input}' and '{output}'
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        ext = input_path.suffix
        
        import tempfile
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir = Path(temp_dir)
            # 1. Split into chunks (10s each)
            chunk_pattern = str(temp_dir / f"chunk_%03d{ext}")
            split_cmd = [
                "-i", str(input_path),
                "-c", "copy",
                "-f", "segment",
                "-segment_time", "10",
                "-reset_timestamps", "1",
                "-map", "0",
                "-y",
                chunk_pattern
            ]
            split_res = run_ffmpeg(split_cmd, ffmpeg_path=self.ffmpeg_path)
            if not split_res.success:
                print(f"Failed to split video: {split_res.error_message}")
                return False

            chunks = sorted(glob.glob(str(temp_dir / f"chunk_*{ext}")))
            encoded_chunks = []
            
            # 2. Distribute workload
            # Simple round-robin strategy for this MVP
            import concurrent.futures
            
            def process_on_worker(chunk_path, worker_url):
                try:
                    with open(chunk_path, "rb") as f:
                        data = xmlrpc.client.Binary(f.read())
                    client = xmlrpc.client.ServerProxy(worker_url, allow_none=True)
                    print(f"Sending {Path(chunk_path).name} to {worker_url}")
                    result = client.process_chunk(data, ext, cmd_template)
                    if result["success"]:
                        out_path = Path(chunk_path).with_name(f"encoded_{Path(chunk_path).name}")
                        with open(out_path, "wb") as f:
                            f.write(result["data"].data if hasattr(result["data"], "data") else result["data"])
                        return out_path
                    else:
                        print(f"Worker {worker_url} failed: {result.get('error')}")
                        return None
                except Exception as e:
                    print(f"RPC error with {worker_url}: {e}")
                    return None

            with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.worker_urls)) as executor:
                futures = {}
                for i, chunk in enumerate(chunks):
                    worker = self.worker_urls[i % len(self.worker_urls)]
                    futures[executor.submit(process_on_worker, chunk, worker)] = chunk
                    
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res:
                        encoded_chunks.append(res)
                    else:
                        print("A chunk failed to encode. Aborting cluster process.")
                        return False

            # Sort encoded chunks back into order
            encoded_chunks.sort(key=lambda x: str(x))

            # 3. Concatenate
            list_file = temp_dir / "concat_list.txt"
            with open(list_file, "w") as f:
                for chunk_path in encoded_chunks:
                    # ffmpeg concat demuxer requires forward slashes or escaped backslashes
                    safe_path = str(chunk_path).replace("\\", "/")
                    f.write(f"file '{safe_path}'\n")

            concat_cmd = [
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-c", "copy",
                "-y",
                str(output_path)
            ]
            concat_res = run_ffmpeg(concat_cmd, ffmpeg_path=self.ffmpeg_path)
            
            if not concat_res.success:
                print(f"Failed to concatenate chunks: {concat_res.error_message}")
                return False
                
            return True
