"""
core/vmaf.py - VMAF (Video Multi-Method Assessment Fusion) utility.
Provides an algorithm for finding the mathematically optimal Constant Rate Factor (CRF)
by doing a binary search over a short 5-second representative sample of the video.
"""

import os
import re
import tempfile
from pathlib import Path
from typing import Callable, Optional

from ffram.core.runner import run_ffmpeg, ProgressInfo


def _extract_sample(input_path: Path, temp_dir: Path, ffmpeg_path: str = "ffmpeg") -> Path:
    """Extract a 5-second sample from the middle of the video using stream-copy."""
    from ffram.core.probe import get_duration
    
    duration = get_duration(input_path, ffprobe_path=ffmpeg_path.replace("ffmpeg", "ffprobe"))
    # Try to grab a sample from the middle (or 30s in if duration is long)
    start_time = min(30.0, max(0.0, duration / 2 - 2.5))
    
    sample_path = temp_dir / "sample.mp4"
    
    cmd = [
        "-ss", str(start_time),
        "-i", str(input_path),
        "-t", "5",
        "-c", "copy",
        "-y",
        str(sample_path)
    ]
    
    res = run_ffmpeg(cmd, ffmpeg_path=ffmpeg_path)
    if res.success and sample_path.exists():
        return sample_path
    raise RuntimeError(f"Failed to extract sample: {res.error_message}")


def _calculate_vmaf(source: Path, encoded: Path, ffmpeg_path: str = "ffmpeg") -> float:
    """Run libvmaf filter and parse the stderr output for the final score."""
    cmd = [
        "-i", str(encoded),
        "-i", str(source),
        "-lavfi", "libvmaf",
        "-f", "null",
        "-"
    ]
    
    # run_ffmpeg captures stderr, so we can parse it from there. 
    # But wait, run_ffmpeg returns error_message if return_code != 0. 
    # libvmaf returns 0 if successful, but prints to stderr. 
    # Let's run a direct subprocess to get the raw stderr.
    
    import subprocess
    full_cmd = [ffmpeg_path, "-i", str(encoded), "-i", str(source), "-lavfi", "libvmaf", "-f", "null", "-"]
    proc = subprocess.run(full_cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
    
    # Parse "VMAF score: 95.32"
    matches = re.findall(r"VMAF score: (\d+(?:\.\d+)?)", proc.stderr)
    if matches:
        return float(matches[-1])
    return 0.0


def suggest_optimal_crf(
    input_path: str | Path,
    target_vmaf: float = 95.0,
    min_crf: int = 15,
    max_crf: int = 35,
    encoder: str = "libx264",
    on_progress: Optional[Callable[[str], None]] = None,
    ffmpeg_path: str = "ffmpeg"
) -> int:
    """
    Perform a binary search to find the highest CRF (smallest file size)
    that achieves the target VMAF score on a 5-second sample.
    """
    input_path = Path(input_path)
    
    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        
        if on_progress:
            on_progress("Extracting 5-second representative sample...")
            
        try:
            sample_source = _extract_sample(input_path, temp_dir, ffmpeg_path)
        except RuntimeError:
            # Fallback if stream copy fails
            if on_progress:
                on_progress("Failed to extract sample, falling back to default CRF.")
            return 23

        low = min_crf
        high = max_crf
        best_crf = 23 # Default
        closest_diff = float('inf')
        
        iteration = 1
        max_iterations = 5
        
        while low <= high and iteration <= max_iterations:
            mid_crf = (low + high) // 2
            
            if on_progress:
                on_progress(f"VMAF Iteration {iteration}: Testing CRF {mid_crf}...")
                
            encoded_sample = temp_dir / f"encoded_{mid_crf}.mp4"
            
            # Encode sample
            cmd = [
                "-i", str(sample_source),
                "-c:v", encoder,
                "-crf", str(mid_crf),
                "-preset", "veryfast", # use veryfast for quick testing
                "-c:a", "copy",
                "-y",
                str(encoded_sample)
            ]
            run_ffmpeg(cmd, ffmpeg_path=ffmpeg_path)
            
            # Calculate VMAF
            score = _calculate_vmaf(sample_source, encoded_sample, ffmpeg_path)
            
            if on_progress:
                on_progress(f"VMAF Iteration {iteration}: CRF {mid_crf} yielded VMAF {score:.2f}")
            
            diff = abs(score - target_vmaf)
            if diff < closest_diff:
                closest_diff = diff
                best_crf = mid_crf

            if diff < 0.5:
                # Close enough
                break
            elif score > target_vmaf:
                # Quality too high, we can increase CRF to reduce bitrate
                low = mid_crf + 1
            else:
                # Quality too low, decrease CRF to increase quality
                high = mid_crf - 1
                
            iteration += 1
            
        return best_crf
