"""Minimal name-keyed registry used for ANDES operators."""

from __future__ import annotations


class Registry:
    """Maps a string name to a registered class or callable."""

    def __init__(self, name: str):
        self._name = name
        self._obj_map: dict = {}

    def register(self, obj=None):
        """Register ``obj`` (or, when used as ``@register()``, the decorated target)."""
        if obj is None:

            def deco(func_or_class):
                self._obj_map[func_or_class.__name__] = func_or_class
                return func_or_class

            return deco

        self._obj_map[obj.__name__] = obj
        return obj

    def get(self, name: str):
        if name not in self._obj_map:
            raise KeyError(f"No object named '{name}' in registry '{self._name}'")
        return self._obj_map[name]

    def __contains__(self, name: str) -> bool:
        return name in self._obj_map


OPERATOR_REGISTRY = Registry(name="operators")
