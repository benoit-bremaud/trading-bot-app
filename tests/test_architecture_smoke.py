def test_domain_entities_import():
    from trading_bot.domain.entities import Candle, PairProfile

    assert Candle.__name__ == "Candle"
    assert PairProfile.__name__ == "PairProfile"


def test_application_ports_import():
    from trading_bot.application import ports

    assert hasattr(ports, "MarketDataProvider")
    assert hasattr(ports, "SignalModel")
