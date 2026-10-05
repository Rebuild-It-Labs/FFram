# Benchmarks & Performance

We regularly benchmark FFram to ensure it maintains high performance, exceptional quality, and robust reliability under pressure.

## Probe Latency (PyAV vs FFprobe)
FFram uses **PyAV** bindings to instantly extract media metadata instead of spawning slower `ffprobe` subprocesses for every file.
* **FFprobe Average Latency**: 52.48 ms
* **PyAV Average Latency**: 9.62 ms
* **Result**: FFram metadata probing is **5.46x faster**.

## Auto-Heuristic Resiliency
FFram includes self-healing logic for common hardware and system faults. We simulate fatal FFmpeg crashes to ensure pipelines don't fail unexpectedly.
* **Out-Of-Memory (OOM)**: When an OOM crash is detected, FFram successfully recovers by applying a `-threads 1` fallback parameter.
* **GPU Encoder Failure (NVENC)**: If hardware encoding fails (e.g., NVENC driver issues), FFram automatically falls back to CPU encoding (`libx264`) seamlessly.

## Auto-CRF & VMAF Quality Control
FFram includes smart encoding operations that use VMAF binary search to guarantee perceptual video quality.
* **High Motion Videos**: Reaches a VMAF target of 96.58 by intelligently allocating bandwidth.
* **Low Motion Videos**: Maintains a strict 96.19 VMAF score, preventing quality degradation.
