# ffram

![PyPI version](https://img.shields.io/pypi/v/ffram)
![Python Versions](https://img.shields.io/pypi/pyversions/ffram)
![License](https://img.shields.io/github/license/ffram/ffram)

**ffram** — **Fast FFmpeg Renderer for Audio and Moving-pictures** 

It is a highly interactive, beautifully styled Terminal User Interface (TUI) for executing complex media operations on Windows, macOS, and Linux.

It simplifies media processing with an intuitive menu system, native file picker dialogs, and real-time progress bars with ETAs and FPS—completely abstracting away complex FFmpeg command-line syntax.

## Features

- **102 High-Performance Media Operations** across **18 Specialized Categories**.
- **Interactive TUI** built with `InquirerPy` and `rich`.
- **Fuzzy Search** to instantly find operations by name or description.
- **Native File Picker Dialogs** (just press Enter to browse visually).
- **GPU Hardware Acceleration Auto-Detection** (NVIDIA NVENC, Intel QSV, AMD AMF).
- **Smart Quality Suggestions** (CRF, bitrates) directly in the UI.
- **Batch Processing** capability.

## Installation

```bash
pip install ffram
```

*Requires Python 3.9+ and FFmpeg installed on your system PATH.*

## Quick Start

Simply run the tool from any terminal:

```bash
ffram
```

## Categories Overview

1. Video to Audio Extraction (7 ops)
2. Audio Track Management (9 ops)
3. Format & Container Conversion (8 ops)
4. Video Compression & Bitrate Control (5 ops)
5. Resolution & Upscale/Downscale (6 ops)
6. Cut, Split & Trim Operations (5 ops)
7. Stream & Track Removal (5 ops)
8. Audio Filters & Volume Normalization (6 ops)
9. Visual Effects & Filters (6 ops)
10. Playback Speed & Frame Rate (6 ops)
11. Frame Extraction & Animated GIFs (6 ops)
12. Concatenation & Video Merging (4 ops)
13. Watermarks & Text Overlays (5 ops)
14. Aspect Ratio & Padding (5 ops)
15. Subtitle Embedding & Extraction (6 ops)
16. Metadata Inspection & Tagging (4 ops)
17. Multi-File Batch Workflows (5 ops)
18. Smart Multi-Step Pipelines (4 ops)

## Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for a 3-step guide on how to add your own FFmpeg operations to the toolkit.

## License

MIT License. See `LICENSE` for details.
