"""Minimal operator registry (no lazy filesystem scan, no rich tables)."""


class Registry:
    def __init__(self, name: str):
        self._name = name
        self._obj_map: dict = {}

    def register(self, obj=None):
        if obj is None:

            def deco(func_or_class):
                self._obj_map[func_or_class.__name__] = func_or_class
                return func_or_class

            return deco

        self._obj_map[obj.__name__] = obj
        return obj

    def get(self, name):
        if name not in self._obj_map:
            raise KeyError(f"No object named '{name}' in registry '{self._name}'")
        return self._obj_map[name]

    def __contains__(self, name):
        return name in self._obj_map


OPERATOR_REGISTRY = Registry(name="operators")
