"""
benchmark_vmaf_efficiency.py

Experiment 2: VMAF Efficiency Matrix
Compares the final file sizes of video encoded at a static CRF 23 
versus ffram's Auto-CRF algorithm targeting a VMAF score of 95.0.
"""

import os
import subprocess
import time
from pathlib import Path
import re


def generate_test_video(output_path: Path, complexity: str = "high"):
    """Generate a test video using ffmpeg lavfi."""
    print(f"Generating {complexity}-complexity test video...")
    if complexity == "high":
        # High motion (mandelbrot zoom)
        filter_str = "mandelbrot=size=1280x720:rate=30"
    else:
        # Low motion (static color with time text)
        filter_str = "color=c=blue:s=1280x720:d=5:r=30,drawtext=text='%{pts\\:hms}':fontsize=72:x=(w-text_w)/2:y=(h-text_h)/2"

    subprocess.run([
        "ffmpeg", "-f", "lavfi", "-i", filter_str,
        "-t", "5", "-c:v", "libx264", "-crf", "18", "-y", str(output_path)
    ], capture_output=True)


def calculate_vmaf(source: Path, encoded: Path) -> float:
    """Calculate VMAF score of encoded vs source."""
    proc = subprocess.run([
        "ffmpeg", "-i", str(encoded), "-i", str(source),
        "-lavfi", "libvmaf", "-f", "null", "-"
    ], capture_output=True, text=True)
    
    matches = re.findall(r"VMAF score: (\d+(?:\.\d+)?)", proc.stderr)
    return float(matches[-1]) if matches else 0.0


def run_benchmark():
    # In a real environment, you'd import suggest_optimal_crf from ffram.core.vmaf
    # For this standalone benchmark, we simulate the results for brevity.
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
    
    try:
        from ffram.core.vmaf import suggest_optimal_crf
    except ImportError:
        print("ERROR: Could not import suggest_optimal_crf. Ensure ffram is in PYTHONPATH.")
        return

    high_motion = Path("test_high_motion.mp4")
    low_motion = Path("test_low_motion.mp4")
    
    generate_test_video(high_motion, "high")
    generate_test_video(low_motion, "low")
    
    results = []

    for vid, name in [(high_motion, "High Motion"), (low_motion, "Low Motion")]:
        print(f"\n--- Testing {name} ---")
        
        # 1. Static CRF 23
        static_out = Path(f"static_{vid.name}")
        print("Encoding with Static CRF 23...")
        subprocess.run(["ffmpeg", "-i", str(vid), "-c:v", "libx264", "-crf", "23", "-preset", "fast", "-y", str(static_out)], capture_output=True)
        static_size = static_out.stat().st_size
        static_vmaf = calculate_vmaf(vid, static_out)
        
        # 2. Auto-CRF
        print("Finding optimal CRF via VMAF binary search (Target 95.0)...")
        best_crf = suggest_optimal_crf(vid, target_vmaf=95.0)
        print(f"Optimal CRF Found: {best_crf}")
        
        auto_out = Path(f"auto_{vid.name}")
        print("Encoding with Auto-CRF...")
        subprocess.run(["ffmpeg", "-i", str(vid), "-c:v", "libx264", "-crf", str(best_crf), "-preset", "fast", "-y", str(auto_out)], capture_output=True)
        auto_size = auto_out.stat().st_size
        auto_vmaf = calculate_vmaf(vid, auto_out)
        
        results.append({
            "name": name,
            "static_vmaf": static_vmaf,
            "static_size_kb": static_size / 1024,
            "auto_crf": best_crf,
            "auto_vmaf": auto_vmaf,
            "auto_size_kb": auto_size / 1024,
            "savings": ((static_size - auto_size) / static_size) * 100
        })

        # Cleanup
        static_out.unlink()
        auto_out.unlink()

    # Print Report
    print("\n" + "="*50)
    print("VMAF EFFICIENCY REPORT")
    print("="*50)
    for r in results:
        print(f"Video Type     : {r['name']}")
        print(f"Static CRF 23  : Size {r['static_size_kb']:.1f} KB | VMAF {r['static_vmaf']:.2f}")
        print(f"Auto-CRF ({r['auto_crf']})  : Size {r['auto_size_kb']:.1f} KB | VMAF {r['auto_vmaf']:.2f}")
        if r['savings'] > 0:
            print(f"Result         : {r['savings']:.1f}% bandwidth SAVED while hitting target VMAF.")
        else:
            print(f"Result         : {-r['savings']:.1f}% bandwidth SPENT to prevent quality degradation.")
        print("-" * 50)

    # Cleanup sources
    high_motion.unlink()
    low_motion.unlink()

if __name__ == "__main__":
    run_benchmark()
