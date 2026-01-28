import json

import pytest

from trading_bot.shared.config import ConfigError, deep_merge, load_config, resolve_pair_config


def test_deep_merge_overrides_nested():
    base = {"risk": {"max_position_pct": 0.02, "limit": 1}, "mode": "a"}
    override = {"risk": {"max_position_pct": 0.05}}

    merged = deep_merge(base, override)

    assert merged["risk"]["max_position_pct"] == 0.05
    assert merged["risk"]["limit"] == 1
    assert merged["mode"] == "a"


def test_resolve_pair_config_precedence():
    raw = {
        "default": {"signal": {"threshold": 0.5}, "risk": {"max_position_pct": 0.02}},
        "timeframes": {"5m": {"signal": {"threshold": 0.6}}},
        "pairs": {"BTC-USDT": {"risk": {"max_position_pct": 0.03}}},
        "pair_timeframe": {"BTC-USDT": {"5m": {"risk": {"max_position_pct": 0.04}}}},
    }

    resolved = resolve_pair_config(raw, "BTC-USDT", "5m")

    assert resolved["signal"]["threshold"] == 0.6
    assert resolved["risk"]["max_position_pct"] == 0.04


def test_validate_config_rejects_non_mapping(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps({"default": []}))

    with pytest.raises(ConfigError):
        load_config(str(path))
