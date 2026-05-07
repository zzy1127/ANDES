"""Abstract base class for LLM serving backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List


class LLMServingABC(ABC):
    """Abstract base class for LLM-serving backends used by ANDES operators."""

    @abstractmethod
    def generate_from_input(
        self, user_inputs: List[str], system_prompt: str
    ) -> List[str]:
        """Generate one response per ``user_inputs`` entry."""

    @abstractmethod
    def start_serving(self) -> None:
        """Start the underlying service if any (no-op for HTTP backends)."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release any resources held by this backend (sockets, GPU memory, ...)."""

    def load_model(self, model_name_or_path: str, **kwargs: Any):
        """Load a local model. Optional; subclasses may override."""
        raise NotImplementedError("This method should be implemented by subclasses.")
