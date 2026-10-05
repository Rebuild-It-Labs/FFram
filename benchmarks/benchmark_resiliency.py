"""
benchmark_resiliency.py

Experiment 4: Resiliency Stress Test
Artificially induces Out-Of-Memory (OOM) and GPU driver failures by injecting
mocked strings into a hijacked subprocess, tracking the success rate of the 
run_ffmpeg Auto-Heuristic Recovery loop.
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

try:
    from ffram.core.runner import run_ffmpeg, RunResult
except ImportError:
    print("ERROR: Could not import ffram runner modules.")
    sys.exit(1)


class MockProcess:
    def __init__(self, stderr_payload: bytes):
        self.returncode = 1
        self.stderr_payload = stderr_payload
        self.read_count = 0

    class MockStderr:
        def __init__(self, payload: bytes, parent):
            self.payload = payload
            self.parent = parent

        def read(self, size):
            if self.parent.read_count == 0:
                self.parent.read_count += 1
                return self.payload
            return b""

    @property
    def stderr(self):
        return self.MockStderr(self.stderr_payload, self)

    def wait(self):
        pass


def run_benchmark():
    print("="*50)
    print("RESILIENCY HEURISTIC TEST (SIMULATED FAULT INJECTION)")
    print("="*50)
    print("Note: This test uses unittest.mock to artificially inject fatal FFmpeg error strings")
    print("to verify the self-healing logic without requiring actual hardware failure.\n")

    # 1. Test OOM Recovery
    print("\n[Test 1] Injecting Simulated Out-Of-Memory Error...")
    
    # We mock subprocess.Popen to return a process that outputs an OOM error on the first try,
    # but succeeds on the second try if it detects the -threads 1 fallback parameter.
    def mock_popen_oom(*args, **kwargs):
        cmd_args = args[0] if args else kwargs.get("args", [])
        if "-threads" in cmd_args and "1" in cmd_args:
            print("  -> SUCCESS: Detected '-threads 1' fallback parameter.")
            # Return success mock
            mock = MockProcess(b"time=00:00:01.00 bitrate=100k")
            mock.returncode = 0
            return mock
        print("  -> Triggering Fake OOM Error...")
        return MockProcess(b"Cannot allocate memory. Fatal error.")

    with patch('subprocess.Popen', side_effect=mock_popen_oom):
        result = run_ffmpeg(["-i", "dummy.mp4", "-c:v", "libx264", "out.mp4"])
        if result.success:
            print("  [PASS] Auto-Heuristic Recovery resolved the OOM crash.")
        else:
            print("  [FAIL] Did not recover.")

    # 2. Test GPU Failure Recovery
    print("\n[Test 2] Injecting Simulated NVENC GPU Encoder Failure...")
    
    def mock_popen_gpu(*args, **kwargs):
        cmd_args = args[0] if args else kwargs.get("args", [])
        # If it swapped h264_nvenc to libx264
        if "libx264" in cmd_args and "h264_nvenc" not in cmd_args:
            print("  -> SUCCESS: Detected CPU fallback (libx264).")
            mock = MockProcess(b"time=00:00:01.00")
            mock.returncode = 0
            return mock
        print("  -> Triggering Fake NVENC Error...")
        return MockProcess(b"No NVENC capable devices found.")

    with patch('subprocess.Popen', side_effect=mock_popen_gpu):
        result = run_ffmpeg(["-i", "dummy.mp4", "-c:v", "h264_nvenc", "out.mp4"])
        if result.success:
            print("  [PASS] Auto-Heuristic Recovery resolved the GPU crash.")
        else:
            print("  [FAIL] Did not recover.")

    print("\n" + "="*50)
    print("ALL TESTS COMPLETE")
    print("="*50)

if __name__ == "__main__":
    run_benchmark()
