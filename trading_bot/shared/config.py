from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class ConfigError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class Config:
    raw: dict[str, Any]

    def for_pair(self, symbol: str, timeframe: str) -> dict[str, Any]:
        return resolve_pair_config(self.raw, symbol, timeframe)


def load_config(path: str | None = None) -> Config:
    config_path = path or os.getenv("TRADING_BOT_CONFIG", "config/config.json")
    if not os.path.exists(config_path):
        return Config(raw={})

    data = _load_file(config_path)
    validate_config(data)
    return Config(raw=data)


def resolve_pair_config(raw: Mapping[str, Any], symbol: str, timeframe: str) -> dict[str, Any]:
    base = dict(raw.get("default", {}))
    base = deep_merge(base, dict(raw.get("timeframes", {}).get(timeframe, {})))
    base = deep_merge(base, dict(raw.get("pairs", {}).get(symbol, {})))
    pair_tf = raw.get("pair_timeframe", {}).get(symbol, {}).get(timeframe, {})
    return deep_merge(base, dict(pair_tf))


def validate_config(raw: Mapping[str, Any]) -> None:
    for key in ("default", "pairs", "timeframes", "pair_timeframe"):
        if key in raw and not isinstance(raw[key], Mapping):
            raise ConfigError(f"'{key}' must be a mapping")


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(base.get(key), Mapping):
            base[key] = deep_merge(dict(base[key]), dict(value))
        else:
            base[key] = value
    return base


def _load_file(path: str) -> dict[str, Any]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    if ext in (".toml", ".tml"):
        import tomllib

        with open(path, "rb") as f:
            return tomllib.load(f)
    if ext in (".yaml", ".yml"):
        try:
            import yaml
        except ImportError as exc:
            raise ConfigError("PyYAML is required to load YAML config files") from exc
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    raise ConfigError(f"Unsupported config extension: {ext}")
