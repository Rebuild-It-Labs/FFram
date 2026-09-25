"""
ui/progress_bar.py - Real-time FFmpeg progress bar using Rich.
Displays percentage, speed, FPS, ETA, and elapsed time.
"""

from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    SpinnerColumn,
    TaskProgressColumn,
)
from rich.console import Console
from ffram.core.runner import ProgressInfo


class FFmpegProgressBar:
    """
    Rich-based progress bar tailored for FFmpeg operations.
    Shows: [spinner] description ━━━━━━ 45.2% • 30fps • 2.1x speed • ETA 00:32
    """

    def __init__(self, description: str = "Processing", console: Console = None):
        self.description = description
        self._console = console or Console()
        self._progress = None
        self._task_id = None
        self._started = False

    def start(self):
        """Start the progress bar display."""
        self._progress = Progress(
            SpinnerColumn("dots", style="bright_cyan"),
            TextColumn("[bold bright_white]{task.description}[/]"),
            BarColumn(
                bar_width=30,
                style="dim white",
                complete_style="bright_cyan",
                finished_style="bright_green",
            ),
            TaskProgressColumn(),
            TextColumn("[dim]|[/]"),
            TextColumn("[bright_yellow]{task.fields[fps]}[/]"),
            TextColumn("[dim]|[/]"),
            TextColumn("[bright_magenta]{task.fields[speed]}[/]"),
            TextColumn("[dim]|[/]"),
            TimeRemainingColumn(),
            console=self._console,
            transient=False,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(
            self.description,
            total=100,
            fps="-- fps",
            speed="--x",
        )
        self._started = True

    def update(self, info: ProgressInfo):
        """Update the progress bar with new FFmpeg progress data."""
        if not self._started or self._progress is None:
            return

        fps_str = f"{info.fps:.0f} fps" if info.fps > 0 else "-- fps"
        speed_str = info.speed if info.speed and info.speed != "N/A" else "--x"

        self._progress.update(
            self._task_id,
            completed=info.percent,
            fps=fps_str,
            speed=speed_str,
        )

    def finish(self):
        """Complete and close the progress bar."""
        if self._started and self._progress is not None:
            self._progress.update(self._task_id, completed=100)
            self._progress.stop()
            self._started = False

    def error(self):
        """Stop progress bar on error."""
        if self._started and self._progress is not None:
            self._progress.stop()
            self._started = False

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        if self._started:
            self.finish()


class IndeterminateProgress:
    """Spinner-only progress for operations where duration is unknown."""

    def __init__(self, description: str = "Processing...", console: Console = None):
        self.description = description
        self._console = console or Console()
        self._progress = None
        self._task_id = None

    def start(self):
        self._progress = Progress(
            SpinnerColumn("dots", style="bright_cyan"),
            TextColumn("[bold bright_white]{task.description}[/]"),
            console=self._console,
            transient=True,
        )
        self._progress.start()
        self._task_id = self._progress.add_task(self.description, total=None)

    def stop(self):
        if self._progress:
            self._progress.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()
