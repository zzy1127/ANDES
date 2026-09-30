"""ANDES — Agent-Native Data Evolving Synthesis.

A lightweight, API-only data synthesis pipeline that combines a dynamic
taxonomy router, a question/answer generator, and a self-critique refiner.
"""

from .logger import get_logger
from .version import __version__, version_info

__all__ = ["__version__", "version_info", "get_logger"]
