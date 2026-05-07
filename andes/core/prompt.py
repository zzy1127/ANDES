"""Prompt base classes and the `prompt_restrict` decorator.

ANDES operators are written against well-defined prompt classes rather than
raw strings. The classes here let an operator declare which prompt types it
accepts via :func:`prompt_restrict`; users can still inject custom prompts by
subclassing :class:`DIYPromptABC`.
"""

from __future__ import annotations

import inspect
from functools import wraps
from typing import TypeVar, Union


class PromptABC:
    """Base class for prompt templates shipped with ANDES."""

    def __init__(self):
        pass

    def build_prompt(self):
        raise NotImplementedError


class DIYPromptABC(PromptABC):
    """Marker base class for user-defined prompts.

    Subclassing this class signals that a prompt should bypass the
    operator-level whitelist enforced by :func:`prompt_restrict`.
    """

    def __init__(self):
        super().__init__()

    def build_prompt(self):
        raise NotImplementedError


def _make_diyprompt_union(allowed_prompts: tuple[type[PromptABC], ...]):
    """Build a ``Union`` type covering ``allowed_prompts`` plus DIY and ``None``."""
    return Union[tuple(allowed_prompts) + (DIYPromptABC, type(None))]


T = TypeVar("T")


def prompt_restrict(*allowed_prompts: type[DIYPromptABC]):
    """Restrict the ``prompt_template`` argument of a class to whitelisted types.

    Applied as a class decorator. Acceptable values for ``prompt_template`` at
    instantiation time are:

      * any of ``allowed_prompts``,
      * any subclass of :class:`DIYPromptABC`, or
      * ``None``.

    A type-annotated ``Union`` is also installed on the class so static
    inspection tools (e.g. ``get_type_hints``) report the same constraint.
    """

    def decorator(cls: T) -> T:
        setattr(cls, "ALLOWED_PROMPTS", tuple(allowed_prompts))

        orig_init = cls.__init__
        # Resolve the signature once at decoration time to avoid re-parsing on
        # every instantiation.
        sig = inspect.signature(orig_init)
        if "prompt_template" not in sig.parameters:
            # No-op: classes that do not accept a `prompt_template` parameter
            # only get the annotation update below.
            pass

        @wraps(orig_init)
        def new_init(self, *args, **kwargs):
            try:
                bound = sig.bind_partial(self, *args, **kwargs)
                bound.apply_defaults()
            except TypeError:
                # Defer to the original __init__ for the canonical error.
                return orig_init(self, *args, **kwargs)

            pt = bound.arguments.get("prompt_template", None)

            if pt is not None and not isinstance(pt, cls.ALLOWED_PROMPTS):
                if not isinstance(pt, DIYPromptABC):
                    allowed_names = "\n".join(
                        f"  - {c.__module__}.{c.__qualname__}"
                        for c in cls.ALLOWED_PROMPTS
                    )
                    raise TypeError(
                        f"[{cls.__name__}] Invalid prompt_template type: "
                        f"{type(pt).__module__}.{type(pt).__qualname__}\n"
                        f"Expected one of:\n{allowed_names}\n"
                        "or a custom subclass of `andes.core.prompt.DIYPromptABC`."
                    )

            return orig_init(self, *args, **kwargs)

        cls.__init__ = new_init

        cls.__annotations__ = dict(getattr(cls, "__annotations__", {}))
        cls.__annotations__["prompt_template"] = _make_diyprompt_union(allowed_prompts)

        return cls

    return decorator


if __name__ == "__main__":
    import pytest

    class A(PromptABC):
        pass

    class B(PromptABC):
        pass

    class MyDIY(DIYPromptABC):
        pass

    class Other(PromptABC):
        pass

    @prompt_restrict(A, B)
    class Op:
        def __init__(self, prompt_template=None):
            self.prompt_template = prompt_template

    Op(prompt_template=A())
    Op(prompt_template=B())
    Op(prompt_template=MyDIY())
    Op()

    Op(A())
    Op(MyDIY())
    with pytest.raises(TypeError):
        Op(Other())

    with pytest.raises(TypeError):
        Op(object())
