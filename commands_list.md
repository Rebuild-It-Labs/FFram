
## 1. Video → Audio

### 1. Extract MP3 from video

```bat
ffmpeg -i input.mp4 -vn  -c:a libmp3lame -q:a 2 output.mp3
```

### 2. Extract WAV

```bat
ffmpeg -i input.mp4 -vn -c:a pcm_s16le output.wav
```

### 3. Extract AAC

```bat
ffmpeg -i input.mp4 -vn -c:a aac -b:a 192k output.aac
```

### 4. Extract M4A

```bat
ffmpeg -i input.mp4 -vn -c:a aac -b:a 192k output.m4a
```

### 5. Extract FLAC

```bat
ffmpeg -i input.mp4 -vn -c:a flac output.flac
```

### 6. Extract OGG

```bat
ffmpeg -i input.mp4 -vn -c:a libvorbis -q:a 5 output.ogg
```

### 7. Extract OPUS

```bat
ffmpeg -i input.mp4 -vn -c:a libopus -b:a 128k output.opus
```

### 8. Extract audio without re-encoding

```bat
ffmpeg -i input.mp4 -vn -c:a copy output.m4a
```

---

# 2. Add / Replace Audio

### 9. Add audio to a silent video

```bat
ffmpeg -i video.mp4 -i audio.mp3 -c:v copy -c:a aac -shortest output.mp4
```

### 10. Add another audio track

```bat
ffmpeg -i video.mp4 -i audio.mp3 -map 0:v -map 0:a? -map 1:a -c:v copy -c:a aac output.mp4
```

### 11. Replace existing video audio

```bat
ffmpeg -i video.mp4 -i newaudio.mp3 -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -shortest output.mp4
```

### 12. Add audio while keeping original audio

```bat
ffmpeg -i video.mp4 -i audio.mp3 -map 0:v -map 0:a? -map 1:a -c:v copy -c:a aac output.mp4
```

### 13. Add audio and loop it if shorter

```bat
ffmpeg -stream_loop -1 -i audio.mp3 -i video.mp4 -map 1:v -map 0:a -c:v copy -c:a aac -shortest output.mp4
```

### 14. Add background music and keep original audio

```bat
ffmpeg -i video.mp4 -i music.mp3 -filter_complex "[0:a][1:a]amix=inputs=2:duration=first" -c:v copy -c:a aac output.mp4
```

### 15. Add background music at 20% volume

```bat
ffmpeg -i video.mp4 -i music.mp3 -filter_complex "[1:a]volume=0.2[m];[0:a][m]amix=inputs=2:duration=first" -c:v copy -c:a aac output.mp4
```

### 16. Replace audio and make video duration match audio

```bat
ffmpeg -i video.mp4 -i audio.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest output.mp4
```

---

# 3. Video Conversion

### 17. MP4 → MKV

```bat
ffmpeg -i input.mp4 -c copy output.mkv
```

### 18. MKV → MP4

```bat
ffmpeg -i input.mkv -c copy output.mp4
```

### 19. MOV → MP4

```bat
ffmpeg -i input.mov -c:v libx264 -c:a aac output.mp4
```

### 20. AVI → MP4

```bat
ffmpeg -i input.avi -c:v libx264 -c:a aac output.mp4
```

### 21. WebM → MP4

```bat
ffmpeg -i input.webm -c:v libx264 -c:a aac output.mp4
```

### 22. MP4 → WebM

```bat
ffmpeg -i input.mp4 -c:v libvpx-vp9 -c:a libopus output.webm
```

### 23. MP4 → MOV

```bat
ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mov
```

### 24. MP4 → AVI

```bat
ffmpeg -i input.mp4 -c:v mpeg4 -c:a mp3 output.avi
```

---

# 4. Compress Video

### 25. Basic compression

```bat
ffmpeg -i input.mp4 -c:v libx264 -crf 28 -c:a aac -b:a 128k output.mp4
```

### 26. High-quality compression

```bat
ffmpeg -i input.mp4 -c:v libx264 -crf 20 -preset medium -c:a aac -b:a 192k output.mp4
```

### 27. Smaller file

```bat
ffmpeg -i input.mp4 -c:v libx264 -crf 30 -c:a aac -b:a 96k output.mp4
```

### 28. H.265 compression

```bat
ffmpeg -i input.mp4 -c:v libx265 -crf 28 -c:a aac -b:a 128k output.mp4
```

### 29. H.265 smaller file

```bat
ffmpeg -i input.mp4 -c:v libx265 -crf 32 -c:a aac -b:a 96k output.mp4
```

### 30. Compress to target bitrate

```bat
ffmpeg -i input.mp4 -b:v 1500k -c:a aac -b:a 128k output.mp4
```

---

# 5. Resize Video

### 31. 1920×1080 → 1280×720

```bat
ffmpeg -i input.mp4 -vf scale=1280:720 output.mp4
```

### 32. Resize to 1080p

```bat
ffmpeg -i input.mp4 -vf scale=-2:1080 output.mp4
```

### 33. Resize to 720p

```bat
ffmpeg -i input.mp4 -vf scale=-2:720 output.mp4
```

### 34. Resize to 480p

```bat
ffmpeg -i input.mp4 -vf scale=-2:480 output.mp4
```

### 35. Resize to 4K

```bat
ffmpeg -i input.mp4 -vf scale=3840:2160 output.mp4
```

### 36. Resize width only

```bat
ffmpeg -i input.mp4 -vf scale=1280:-2 output.mp4
```

### 37. Resize and compress

```bat
ffmpeg -i input.mp4 -vf scale=-2:720 -c:v libx264 -crf 28 -c:a aac output.mp4
```

---

# 6. Cut / Trim Video

### 38. Cut first 30 seconds

```bat
ffmpeg -i input.mp4 -t 30 -c copy output.mp4
```

### 39. Start at 1 minute

```bat
ffmpeg -ss 00:01:00 -i input.mp4 -c copy output.mp4
```

### 40. Cut from 1:00 to 2:30

```bat
ffmpeg -ss 00:01:00 -to 00:02:30 -i input.mp4 -c copy output.mp4
```

### 41. Cut 30-second clip

```bat
ffmpeg -ss 00:01:00 -i input.mp4 -t 30 -c copy output.mp4
```

### 42. Accurate re-encoded cut

```bat
ffmpeg -ss 00:01:00 -i input.mp4 -t 30 -c:v libx264 -c:a aac output.mp4
```

---

# 7. Remove Video / Remove Audio

### 43. Remove audio

```bat
ffmpeg -i input.mp4 -an -c:v copy output.mp4
```

### 44. Remove video

```bat
ffmpeg -i input.mp4 -vn -c:a copy output.m4a
```

### 45. Create silent video

```bat
ffmpeg -i input.mp4 -an output.mp4
```

---

# 8. Change Audio

### 46. Increase volume

```bat
ffmpeg -i input.mp4 -af volume=2 -c:v copy output.mp4
```

### 47. Decrease volume

```bat
ffmpeg -i input.mp4 -af volume=0.5 -c:v copy output.mp4
```

### 48. Convert audio to mono

```bat
ffmpeg -i input.mp4 -ac 1 output.mp4
```

### 49. Convert audio to stereo

```bat
ffmpeg -i input.mp4 -ac 2 output.mp4
```

### 50. Change audio sample rate

```bat
ffmpeg -i input.mp4 -ar 44100 output.mp4
```

### 51. Normalize audio

```bat
ffmpeg -i input.mp4 -af loudnorm -c:v copy output.mp4
```

### 52. Fade audio in

```bat
ffmpeg -i input.mp4 -af "afade=t=in:st=0:d=3" output.mp4
```

### 53. Fade audio out

```bat
ffmpeg -i input.mp4 -af "afade=t=out:st=27:d=3" output.mp4
```

---

# 9. Video Effects

### 54. Rotate 90° clockwise

```bat
ffmpeg -i input.mp4 -vf "transpose=1" output.mp4
```

### 55. Rotate 90° counter-clockwise

```bat
ffmpeg -i input.mp4 -vf "transpose=2" output.mp4
```

### 56. Rotate 180°

```bat
ffmpeg -i input.mp4 -vf "transpose=1,transpose=1" output.mp4
```

### 57. Flip horizontally

```bat
ffmpeg -i input.mp4 -vf hflip output.mp4
```

### 58. Flip vertically

```bat
ffmpeg -i input.mp4 -vf vflip output.mp4
```

### 59. Black & white

```bat
ffmpeg -i input.mp4 -vf format=gray output.mp4
```

### 60. Blur video

```bat
ffmpeg -i input.mp4 -vf "boxblur=10:1" output.mp4
```

### 61. Sharpen video

```bat
ffmpeg -i input.mp4 -vf unsharp=5:5:1.0 output.mp4
```

### 62. Increase brightness

```bat
ffmpeg -i input.mp4 -vf "eq=brightness=0.1" output.mp4
```

### 63. Increase contrast

```bat
ffmpeg -i input.mp4 -vf "eq=contrast=1.5" output.mp4
```

### 64. Adjust saturation

```bat
ffmpeg -i input.mp4 -vf "eq=saturation=1.5" output.mp4
```

---

# 10. Video Speed

### 65. 2× video speed

```bat
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=0.5*PTS[v];[0:a]atempo=2[a]" -map "[v]" -map "[a]" output.mp4
```

### 66. 0.5× slow motion

```bat
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=2*PTS[v];[0:a]atempo=0.5[a]" -map "[v]" -map "[a]" output.mp4
```

### 67. 1.5× speed

```bat
ffmpeg -i input.mp4 -filter_complex "[0:v]setpts=PTS/1.5[v];[0:a]atempo=1.5[a]" -map "[v]" -map "[a]" output.mp4
```

---

# 11. Screenshots / Images

### 68. Extract one frame

```bat
ffmpeg -i input.mp4 -ss 00:00:10 -frames:v 1 screenshot.png
```

### 69. Extract frame every 10 seconds

```bat
ffmpeg -i input.mp4 -vf fps=1/10 frame_%04d.png
```

### 70. Extract one frame per second

```bat
ffmpeg -i input.mp4 -vf fps=1 frame_%04d.jpg
```

### 71. Video → animated GIF

```bat
ffmpeg -i input.mp4 -vf "fps=10,scale=640:-1" output.gif
```

### 72. GIF → MP4

```bat
ffmpeg -i input.gif -movflags faststart -pix_fmt yuv420p output.mp4
```

---

# 12. Combine Videos

### 73. Concatenate MP4 files

Create `list.txt`:

```text
file 'video1.mp4'
file 'video2.mp4'
file 'video3.mp4'
```

Then:

```bat
ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4
```

### 74. Concatenate different videos

```bat
ffmpeg -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac output.mp4
```

### 75. Join two videos using filter_complex

```bat
ffmpeg -i video1.mp4 -i video2.mp4 -filter_complex "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" output.mp4
```

---

# 13. Overlay / Watermark

### 76. Add image watermark

```bat
ffmpeg -i input.mp4 -i logo.png -filter_complex "overlay=10:10" output.mp4
```

### 77. Watermark bottom-right

```bat
ffmpeg -i input.mp4 -i logo.png -filter_complex "overlay=W-w-10:H-h-10" output.mp4
```

### 78. Semi-transparent watermark

```bat
ffmpeg -i input.mp4 -i logo.png -filter_complex "[1:v]format=rgba,colorchannelmixer=aa=0.5[logo];[0:v][logo]overlay=10:10" output.mp4
```

### 79. Add text

```bat
ffmpeg -i input.mp4 -vf "drawtext=text='My Video':x=50:y=50:fontsize=40:fontcolor=white" output.mp4
```

### 80. Add timestamp

```bat
ffmpeg -i input.mp4 -vf "drawtext=text='%{pts\:hms}':x=20:y=20:fontsize=30:fontcolor=white" output.mp4
```

---

# 14. Crop / Aspect Ratio

### 81. Crop video

```bat
ffmpeg -i input.mp4 -vf "crop=1280:720" output.mp4
```

### 82. Center crop to square

```bat
ffmpeg -i input.mp4 -vf "crop=min(iw\,ih):min(iw\,ih)" output.mp4
```

### 83. 16:9 → 9:16

```bat
ffmpeg -i input.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" output.mp4
```

### 84. 16:9 → 1:1

```bat
ffmpeg -i input.mp4 -vf "crop=ih:ih,scale=1080:1080" output.mp4
```

### 85. Add black bars

```bat
ffmpeg -i input.mp4 -vf "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:black" output.mp4
```

---

# 15. Subtitle Commands

### 86. Add SRT subtitles permanently

```bat
ffmpeg -i input.mp4 -vf "subtitles=subtitles.srt" output.mp4
```

### 87. Add selectable subtitle track

```bat
ffmpeg -i input.mp4 -i subtitles.srt -c:v copy -c:a copy -c:s mov_text output.mp4
```

### 88. Extract subtitles

```bat
ffmpeg -i input.mkv -map 0:s:0 subtitles.srt
```

### 89. Remove subtitles

```bat
ffmpeg -i input.mkv -map 0:v -map 0:a -c copy output.mkv
```

---

# 16. Metadata / Information

### 90. Show media information

```bat
ffmpeg -i input.mp4
```

Better for detailed information:

```bat
ffprobe input.mp4
```

### 91. Remove metadata

```bat
ffmpeg -i input.mp4 -map_metadata -1 -c copy output.mp4
```

### 92. Set title metadata

```bat
ffmpeg -i input.mp4 -metadata title="My Video" -c copy output.mp4
```

### 93. Set artist

```bat
ffmpeg -i input.mp4 -metadata artist="My Name" -c copy output.mp4
```

---

# 17. Useful Windows Batch Commands

### 94. Convert every MP4 to MP3

Create `convert.bat`:

```bat
@echo off
for %%F in (*.mp4) do (
    ffmpeg -i "%%F" -vn -c:a libmp3lame -q:a 2 "%%~nF.mp3"
)
pause
```

### 95. Convert every MP4 to 720p

```bat
@echo off
for %%F in (*.mp4) do (
    ffmpeg -i "%%F" -vf scale=-2:720 -c:v libx264 -crf 23 -c:a aac "%%~nF_720p.mp4"
)
pause
```

### 96. Compress every MP4

```bat
@echo off
for %%F in (*.mp4) do (
    ffmpeg -i "%%F" -c:v libx264 -crf 28 -c:a aac -b:a 128k "%%~nF_compressed.mp4"
)
pause
```

### 97. Extract audio from every video

```bat
@echo off
for %%F in (*.mp4) do (
    ffmpeg -i "%%F" -vn -c:a copy "%%~nF.m4a"
)
pause
```

### 98. Add the same audio to every video

```bat
@echo off
for %%F in (*.mp4) do (
    ffmpeg -i "%%F" -i music.mp3 -map 0:v -map 1:a -c:v copy -c:a aac -shortest "%%~nF_new.mp4"
)
pause
```

---

## A few important Windows tips

For paths containing spaces, always use quotes:

```bat
ffmpeg -i "C:\My Videos\input video.mp4" output.mp4
```

If FFmpeg isn't recognized:

```bat
ffmpeg -version
```

For a video where you **want to preserve the original video quality**, use:

```bat
-c:v copy
```
