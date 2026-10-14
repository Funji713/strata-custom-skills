"""Evidence-grounded architecture visualizer."""

from pathlib import Path

__version__ = "1.0.0"
PACKAGE_ROOT = Path(__file__).resolve().parents[1]

from .pipeline import PipelineOptions, run_pipeline

__all__ = ["PipelineOptions", "run_pipeline", "__version__"]
