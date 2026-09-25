"""
operations/base.py - Abstract base class for all FFmpeg operations.
Each operation defines its parameters, builds the FFmpeg command, and executes it.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any


@dataclass
class OperationResult:
    """Result of an operation execution."""
    success: bool
    message: str
    output_path: Optional[Path] = None
    elapsed_seconds: float = 0.0
    command: str = ""


@dataclass
class OperationInfo:
    """Metadata for a single operation."""
    id: int
    name: str
    description: str
    category: str
    needs_second_input: bool = False
    second_input_label: str = ""
    second_input_types: list = field(default_factory=list)


class BaseOperation(ABC):
    """Abstract base class for FFmpeg operations."""

    @abstractmethod
    def get_operations(self) -> list[OperationInfo]:
        """Return list of available operations in this module."""
        pass

    @abstractmethod
    def execute(self, operation_id: int, params: dict) -> OperationResult:
        """
        Execute a specific operation.
        
        Args:
            operation_id: The ID of the operation to run.
            params: Dictionary containing:
                - input_path: Path to input file
                - output_path: Path to output file
                - duration: Duration in seconds (from probe)
                - Additional operation-specific parameters
        
        Returns:
            OperationResult with success status and details.
        """
        pass

    def get_operation_by_id(self, operation_id: int) -> Optional[OperationInfo]:
        """Find an operation by its ID."""
        for op in self.get_operations():
            if op.id == operation_id:
                return op
        return None

    def _build_output_path(self, input_path: Path, suffix: str, new_ext: str = None) -> Path:
        """Helper to build output path with suffix."""
        ext = new_ext if new_ext else input_path.suffix
        if not ext.startswith("."):
            ext = "." + ext
        output = input_path.parent / f"{input_path.stem}{suffix}{ext}"
        counter = 1
        while output.exists():
            output = input_path.parent / f"{input_path.stem}{suffix}_{counter}{ext}"
            counter += 1
        return output
