from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol


class MetricsRecorder(Protocol):
    def increment(self, name: str, value: int = 1, **tags: Any) -> None: ...

    def gauge(self, name: str, value: float, **tags: Any) -> None: ...


def _tag_key(tags: Mapping[str, Any]) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, str(value)) for key, value in tags.items()))


@dataclass(slots=True)
class InMemoryMetrics:
    counters: dict[tuple[str, tuple[tuple[str, str], ...]], int] = field(default_factory=dict)
    gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = field(default_factory=dict)

    def increment(self, name: str, value: int = 1, **tags: Any) -> None:
        key = (name, _tag_key(tags))
        self.counters[key] = self.counters.get(key, 0) + value

    def gauge(self, name: str, value: float, **tags: Any) -> None:
        key = (name, _tag_key(tags))
        self.gauges[key] = value


class NoopMetrics:
    def increment(self, name: str, value: int = 1, **tags: Any) -> None:
        return None

    def gauge(self, name: str, value: float, **tags: Any) -> None:
        return None
