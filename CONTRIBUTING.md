# Contributing to ffram

Thank you for your interest in contributing to ffram! This project is designed to be highly modular so anyone can add new FFmpeg commands and filters without needing to touch the core engine.

## Architecture

The project uses a standard `src/ffram` layout. 
All operations are stored in `src/ffram/categories/`.

## How to Add a New Operation (3 Steps)

### Step 1: Create or Edit a Category Module
If your operation fits an existing category (e.g. `video_effects`), open `src/ffram/categories/video_effects/operations.py`.
If it's entirely new, create a new folder (e.g. `src/ffram/categories/my_category/`) and add an `operations.py` and `__init__.py`.

### Step 2: Register the Operation
Inside `operations.py`, locate the `get_operations(self)` method and add your new `OperationInfo`:

```python
OperationInfo(
    id=200, 
    name="Convert to Black and White", 
    description="Remove all color from video (Grayscale)", 
    category="My Category"
)
```

### Step 3: Implement the FFmpeg Command
In the `execute(self, operation_id, params)` method, handle your new `operation_id` by passing arguments to `print_command` and `run_ffmpeg`:

```python
if operation_id == 200:
    output_path = params.get("output_path") or self._build_output_path(input_path, "_bw", ".mp4")
    cmd_args = ["-i", str(input_path), "-vf", "hue=s=0", str(output_path)]
    
    print_command(["ffmpeg", "-y"] + cmd_args)
    
    progress = FFmpegProgressBar(description="Applying Black and White effect")
    progress.start()
    
    result = run_ffmpeg(cmd_args, duration=params.get("duration"), on_progress=progress.update)
    
    if result.success:
        progress.finish()
        return OperationResult(True, f"Success -> {output_path.name}", output_path, result.elapsed_seconds, result.command)
    
    progress.error()
    return OperationResult(False, f"Failed: {result.error_message}", command=result.command)
```

That's it! Your operation will now automatically appear in the TUI, have fuzzy search capabilities, and include a progress bar.

## Running Tests Locally
Ensure the project loads correctly by running:
```bash
python -m ffram
```
