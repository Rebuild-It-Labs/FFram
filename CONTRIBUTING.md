# Contributing to ffram

ffram is designed to be highly modular so anyone can add new FFmpeg commands and filters without needing to touch the core engine.

## Architecture

The project uses a standard `src/ffram` layout. All operations are stored in `src/ffram/categories/`.

## How to Add a New Operation

### Step 1: Create or Edit a Category Module
If your operation fits an existing category (e.g. `video_fx`), open `src/ffram/categories/video_fx/operations.py`. If it's entirely new, create a new folder and add an `operations.py` and `__init__.py`.

### Step 2: Register the Operation
Inside `operations.py`, locate the `get_operations(self)` method and add your new `OperationInfo`:

```python
OperationInfo(
    id=200, 
    name="Convert to Black and White", 
    description="Remove all color from video", 
    category="Video Effects"
)
```

### Step 3: Implement the FFmpeg Command
In the `execute(self, operation_id, params)` method, add your command to the `cmd_map` and return `self.run_map()`:

```python
def execute(self, operation_id, params):
    input_path = Path(params["input_path"])
    i = str(input_path)
    
    cmd_map = {
        200: (["-i", i, "-vf", "hue=s=0"], "_bw", ".mp4"),
    }
    
    return self.run_map(operation_id, params, cmd_map, "Applying effect")
```

Your operation will automatically appear in the TUI, have fuzzy search capabilities, and include a progress bar.

## Running Locally

To test your changes, run:
```bash
python -m ffram
```
