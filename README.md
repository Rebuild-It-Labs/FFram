# ffram

Fast FFmpeg Renderer for Audio and Moving-pictures

ffram is a fast, highly interactive Terminal User Interface (TUI) for executing complex media operations on Windows, macOS, and Linux. It abstracts complex FFmpeg command-line syntax into an intuitive menu system with native file picker dialogs, real-time progress bars, and ETA calculations.

## Features

- 102 High-Performance Media Operations across 18 Specialized Categories
- Interactive TUI built with InquirerPy and rich
- Fuzzy Search to instantly find operations by name or description
- Native File Picker Dialogs (press Enter to browse visually)
- GPU Hardware Acceleration Auto-Detection (NVIDIA NVENC, Intel QSV, AMD AMF)
- Smart Quality Suggestions directly in the UI
- Batch Processing capability

## Installation

```bash
pip install ffram
```

*Requires Python 3.9+ and FFmpeg installed on your system PATH.*

## Usage

Run the tool from any terminal:

```bash
ffram
```

Or pass a file directly:

```bash
ffram -f "C:\path\to\video.mp4"
```

## Contributing

See `CONTRIBUTING.md` for a guide on how to add your own FFmpeg operations to the toolkit using our streamlined BaseOperation architecture.

## License

MIT License. See `LICENSE` for details.
