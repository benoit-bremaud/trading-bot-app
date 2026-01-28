import logging

from trading_bot.shared.logging import configure_logging, get_logger
from trading_bot.shared.metrics import InMemoryMetrics


def test_context_logger_merges_context(caplog):
    configure_logging(level="INFO", json_output=False)
    logger = get_logger("test").bind(run_id="abc")

    with caplog.at_level(logging.INFO):
        logger.info("hello", step="ingest")

    record = caplog.records[-1]
    assert record.context["run_id"] == "abc"
    assert record.context["step"] == "ingest"


def test_in_memory_metrics_counters_and_gauges():
    metrics = InMemoryMetrics()

    metrics.increment("signals", 2, symbol="BTC-USDT")
    metrics.increment("signals", 1, symbol="BTC-USDT")
    metrics.gauge("latency_ms", 12.5, source="kucoin")

    counter_key = ("signals", (("symbol", "BTC-USDT"),))
    gauge_key = ("latency_ms", (("source", "kucoin"),))

    assert metrics.counters[counter_key] == 3
    assert metrics.gauges[gauge_key] == 12.5
