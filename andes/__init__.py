"""ANDES — Agent-Native Data Evolving Synthesis.

A feedback-controlled experience-acquisition framework for autonomous LLM
post-training, built around a self-evolving World Tree and synthesis reports.
"""

from .logger import get_logger
from .version import __version__, version_info

__all__ = ["__version__", "version_info", "get_logger"]
