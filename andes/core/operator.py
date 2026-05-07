"""Operator base class and registry-backed factory."""

from __future__ import annotations

from abc import ABC, abstractmethod

from andes.logger import get_logger

from .prompt import DIYPromptABC, PromptABC


class OperatorABC(ABC):
    """Base class for ANDES operators.

    Subclasses must implement :meth:`run`. Setting ``ALLOWED_PROMPTS`` (or
    using :func:`andes.core.prompt.prompt_restrict`) lets the operator declare
    which prompt template classes it accepts.
    """

    def __init__(self):
        self.logger = get_logger()
        self.ALLOWED_PROMPTS = tuple([type[DIYPromptABC | PromptABC]])

    @abstractmethod
    def run(self) -> None:
        """Execute the operator. Implementations consume and produce data through
        a :class:`andes.utils.storage.StorageABC` instance.
        """


def get_operator(operator_name: str, args) -> OperatorABC:
    """Look up an operator class by name and instantiate it with ``args``."""
    from andes.utils import OPERATOR_REGISTRY

    operator_cls = OPERATOR_REGISTRY.get(operator_name)
    operator = operator_cls(args)
    logger = get_logger()
    if operator is not None:
        logger.info(f"Successfully created operator {operator_name} with args {args}")
    else:
        logger.error(f"Operator {operator_name} could not be created")
    assert operator is not None
    return operator
