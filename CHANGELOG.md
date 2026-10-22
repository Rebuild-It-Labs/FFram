# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.3] - 2026-10-04
### Added
- Top-Bottom Collage Comparison (Operation 104): Stack two videos vertically for visual quality comparison with filename labels overlaid at the top end of each video, automatic aspect-ratio scaling, and optional colored divider line.
- Multi-audio track management (Operation 103): Select and extract a specific audio track from videos with multiple audio streams and losslessly remux it into a target video (options for only new audio, secondary track, primary default, or specific track replacement).
- Comprehensive Muxing & Interleaving Fix across all operations:
  - Enforced `-max_interleave_delta 0` and `-max_muxing_queue_size 2048` across all multi-input, stream-copy, and remuxing operations (Operations 9-16, 17-18, 38-41, 46-51, 73, 87, 89, 91-93, 98, 103) preventing audio packet buffer starvation and player freezing caused by sparse tracks (e.g. PGS subtitles).
  - Centralized defensive sanitization in `BaseOperation.run_op` ensuring automatic `-movflags +faststart` for all MP4/MOV outputs and automatic interleaver protection for multi-input / stream-copy workflows.
  - Implemented auto-heuristic recovery in `run_ffmpeg` to automatically catch buffer queue overflow errors and retry with expanded buffer queues (`-max_muxing_queue_size 9999 -max_interleave_delta 0`).
  - Added `-avoid_negative_ts make_zero` to stream-copy cut operations (38-41) to eliminate initial freeze and black frames.
- Enhanced Media Quality Inspector & CLI (`ffram info <file>` / `ffram -i <file>` / Operation 90):
  - Intelligent automatic resolution classification (`1080p Full HD`, `1440p 2K QHD`, `4K UHD`, `8K UHD`, `720p HD`) supporting standard 16:9, cinemascope (2.39:1 / 2.35:1), and ultrawide video ratios.
  - Automatic Dynamic Range & Color Depth detection (`HDR10`, `HLG`, `SDR`, `10-bit`, `12-bit`, `8-bit`).
  - Comprehensive multi-track audio inspection displaying codec, channel layout (e.g. `5.1(side)`, `Stereo`), sample rates, bitrates, language tags, and track names.
  - Subtitle track inspection listing format types and languages.
  - Pure audio file inspection displaying format, sample rate, channels, bitrates, and duration.
- Enhanced stream probing with `audio_streams` detection, channel layout, and descriptive track summaries.
- New responsive website with dark-mode support and SEO optimizations.
- Contribution guidelines and pull request templates.
- Markdown documentation generation using MkDocs.

## [1.0.0] - 2026-10-04
### Added
- Initial release of FFram TUI application.
- 102 High-performance FFmpeg operations.
- Native file pickers for Windows.
