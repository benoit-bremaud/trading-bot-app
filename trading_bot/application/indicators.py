from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from trading_bot.domain.entities import Candle, EnrichedCandle, Indicator


class IndicatorCalculator(Protocol):
    """Port pour calculer un indicateur technique sur une série de candles"""

    @property
    def name(self) -> str:
        """Nom de l'indicateur (ex: 'RSI_14', 'MACD_12_26_9')"""
        ...

    def min_periods(self) -> int:
        """Nombre minimum de candles requis pour calculer l'indicateur"""
        ...

    def calculate(self, candles: Sequence[Candle]) -> Sequence[Indicator]:
        """
        Calcule l'indicateur pour chaque candle (où applicable).
        Retourne une séquence d'Indicator alignée avec les candles.
        """
        ...


class IndicatorPipeline(Protocol):
    """Port pour orchestrer le calcul de plusieurs indicateurs"""

    def add_indicator(self, calculator: IndicatorCalculator) -> None:
        """Ajoute un calculateur d'indicateur au pipeline"""
        ...

    def enrich(self, candles: Sequence[Candle]) -> Sequence[EnrichedCandle]:
        """
        Enrichit les candles avec tous les indicateurs configurés.
        Retourne une séquence d'EnrichedCandle avec les indicateurs calculés.
        """
        ...
