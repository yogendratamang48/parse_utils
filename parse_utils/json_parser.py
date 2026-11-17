"""Extract dictionaries from JSON-like data using key paths."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, Union

__all__ = ["JsonParser", "JsonPath"]

#: A path is a single key, or a list of keys (str) and list indices (int).
#: A field is one path or a list of fallback paths, e.g.
#: ``"name"``, ``["address", "city"]``, ``[["a", 0], ["b"]]``.
JsonPath = Union[str, Sequence[Union[str, int]]]

_MISSING = object()


def _parse_paths(key: str, spec: Any) -> list[Sequence[str | int]]:
    if isinstance(spec, str):
        return [[spec]]
    if not isinstance(spec, Sequence) or not spec:
        raise ValueError(f"Field {key!r}: expected a key, a path, or a list of paths")
    if all(isinstance(p, (list, tuple)) for p in spec):
        paths = list(spec)
    elif not any(isinstance(p, (list, tuple)) for p in spec):
        paths = [spec]
    else:
        raise ValueError(f"Field {key!r}: cannot mix path steps and fallback paths")

    for path in paths:
        if not path or not all(isinstance(s, (str, int)) and not isinstance(s, bool) for s in path):
            raise ValueError(f"Field {key!r}: path steps must be str keys or int indices")
    return paths


def _resolve(data: Any, path: Sequence[str | int]) -> Any:
    current = data
    for step in path:
        if isinstance(current, Mapping):
            current = current.get(step, _MISSING)
        elif (
            isinstance(current, Sequence) and not isinstance(current, (str, bytes)) and isinstance(step, int)
        ):
            try:
                current = current[step]
            except IndexError:
                return _MISSING
        else:
            return _MISSING
        if current is _MISSING:
            return _MISSING
    return current


class JsonParser:
    """Extracts dicts from parsed JSON (dicts/lists)."""

    def __init__(self, data: Any) -> None:
        self.data = data

    @classmethod
    def from_string(cls, text: str | bytes) -> JsonParser:
        return cls(json.loads(text))

    def extract_dict(
        self, config: Mapping[str, Any], item: Mapping[str, Any] | None = None
    ) -> dict[str, Any]:
        """Build a dict from ``config``, which maps output keys to paths.

        Fallback paths are tried in order; the first that resolves to a value
        other than ``None`` wins. Falsy values such as ``0`` and ``False`` are
        kept. Paths that don't resolve are skipped, and the key is left out.
        """
        result = dict(item or {})
        for key, spec in config.items():
            for path in _parse_paths(key, spec):
                value = _resolve(self.data, path)
                if value is not _MISSING and value is not None:
                    result[key] = value
                    break
        return result
