"""
benchmark_latency.py

Experiment 1: Latency Benchmark (PyAV vs. FFprobe)
Measures the milliseconds required to extract metadata from media files.
This script compares the traditional `subprocess.run(ffprobe)` method against 
the memory-safe native C-bindings provided by `PyAV`.
"""

import time
import subprocess
import json
import statistics
from pathlib import Path

# Try to import PyAV
try:
    import av
    HAS_AV = True
except ImportError:
    HAS_AV = False
    print("WARNING: PyAV ('av') is not installed. PyAV benchmark will be skipped.")


def probe_with_ffprobe(file_path: Path) -> dict:
    """Extract metadata using the traditional ffprobe subprocess method."""
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("ffprobe failed")
    data = json.loads(result.stdout)
    return data


def probe_with_pyav(file_path: Path) -> dict:
    """Extract metadata instantly using memory-safe PyAV bindings."""
    with av.open(str(file_path)) as container:
        video_stream = next((s for s in container.streams if s.type == 'video'), None)
        return {
            "duration": float(container.duration / av.time_base) if container.duration else 0.0,
            "width": video_stream.codec_context.width if video_stream and video_stream.codec_context else 0,
            "height": video_stream.codec_context.height if video_stream and video_stream.codec_context else 0,
        }


def run_benchmark(test_file: Path, iterations: int = 50):
    print(f"--- Starting Latency Benchmark ---")
    print(f"Target file: {test_file.name}")
    print(f"Iterations: {iterations}\n")

    # 1. Benchmark FFprobe
    ffprobe_times = []
    print("Running FFprobe benchmark...")
    for _ in range(iterations):
        start = time.perf_counter()
        probe_with_ffprobe(test_file)
        ffprobe_times.append((time.perf_counter() - start) * 1000)  # ms

    ffprobe_avg = statistics.mean(ffprobe_times)
    ffprobe_std = statistics.stdev(ffprobe_times) if len(ffprobe_times) > 1 else 0.0
    print(f"FFprobe Average: {ffprobe_avg:.2f} ms (±{ffprobe_std:.2f} ms)")

    # 2. Benchmark PyAV
    pyav_avg = 0
    if HAS_AV:
        pyav_times = []
        print("Running PyAV benchmark...")
        for _ in range(iterations):
            start = time.perf_counter()
            probe_with_pyav(test_file)
            pyav_times.append((time.perf_counter() - start) * 1000)  # ms

        pyav_avg = statistics.mean(pyav_times)
        pyav_std = statistics.stdev(pyav_times) if len(pyav_times) > 1 else 0.0
        print(f"PyAV Average:    {pyav_avg:.2f} ms (±{pyav_std:.2f} ms)")
        
        speedup = ffprobe_avg / pyav_avg if pyav_avg > 0 else 0
        print(f"\nResult: PyAV is {speedup:.2f}x faster than FFprobe.")
    else:
        print("Skipping PyAV benchmark.")


if __name__ == "__main__":
    # Ensure a test file exists
    test_video = Path("benchmark_sample.mp4")
    if not test_video.exists():
        print("Creating a 1-second dummy video for testing...")
        subprocess.run([
            "ffmpeg", "-f", "lavfi", "-i", "testsrc=duration=1:size=1280x720:rate=30",
            "-c:v", "libx264", "-y", str(test_video)
        ], capture_output=True)

    run_benchmark(test_video, iterations=20)
    
    # Cleanup
    if test_video.exists():
        try:
            test_video.unlink()
        except:
            pass
