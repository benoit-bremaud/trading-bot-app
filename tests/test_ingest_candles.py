"""Tests pour le script d'ingestion de bougies."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from scripts.ingest_candles import main
from trading_bot.domain.entities import Candle


class TestIngestCandles:
    """Tests pour le script ingest_candles."""

    @patch("scripts.ingest_candles.KucoinMarketDataProvider")
    @patch("scripts.ingest_candles.CsvCandleRepository")
    def test_main_success(self, mock_repo_class, mock_provider_class):
        """Test l'exécution réussie du script d'ingestion."""
        # Configuration des mocks
        mock_provider = MagicMock()
        mock_repo = MagicMock()
        mock_provider_class.return_value = mock_provider
        mock_repo_class.return_value = mock_repo

        # Création de bougies de test
        base_time = datetime(2024, 1, 1, tzinfo=UTC)
        test_candles = [
            Candle(
                timestamp=base_time + timedelta(hours=i),
                open=100.0 + i,
                high=105.0 + i,
                low=95.0 + i,
                close=102.0 + i,
                volume=1000.0,
            )
            for i in range(5)
        ]
        mock_provider.get_ohlcv.return_value = test_candles

        # Exécution avec arguments par défaut
        with patch(
            "sys.argv",
            ["ingest_candles.py", "--symbol", "BTC-USDT", "--days", "7"],
        ):
            result = main()

        # Vérifications
        assert result == 0
        mock_provider.get_ohlcv.assert_called_once()
        mock_repo.save.assert_called_once()

        # Vérifier les arguments de save
        call_args = mock_repo.save.call_args
        assert call_args[0][0] == "BTC-USDT"  # symbol
        assert call_args[0][1] == "1h"  # timeframe
        assert len(call_args[0][2]) == 5  # candles

    @patch("scripts.ingest_candles.KucoinMarketDataProvider")
    @patch("scripts.ingest_candles.CsvCandleRepository")
    def test_main_no_candles(self, mock_repo_class, mock_provider_class):
        """Test le comportement quand aucune bougie n'est récupérée."""
        mock_provider = MagicMock()
        mock_repo = MagicMock()
        mock_provider_class.return_value = mock_provider
        mock_repo_class.return_value = mock_repo

        # Aucune bougie retournée
        mock_provider.get_ohlcv.return_value = []

        with patch(
            "sys.argv",
            ["ingest_candles.py", "--symbol", "ETH-USDT"],
        ):
            result = main()

        # Devrait retourner 1 (échec)
        assert result == 1
        mock_repo.save.assert_not_called()

    @patch("scripts.ingest_candles.KucoinMarketDataProvider")
    @patch("scripts.ingest_candles.CsvCandleRepository")
    def test_main_with_custom_args(self, mock_repo_class, mock_provider_class):
        """Test avec des arguments personnalisés."""
        mock_provider = MagicMock()
        mock_repo = MagicMock()
        mock_provider_class.return_value = mock_provider
        mock_repo_class.return_value = mock_repo

        base_time = datetime(2024, 1, 1, tzinfo=UTC)
        test_candles = [Candle(base_time, 100.0, 105.0, 95.0, 102.0, 1000.0)]
        mock_provider.get_ohlcv.return_value = test_candles

        with patch(
            "sys.argv",
            [
                "ingest_candles.py",
                "--symbol",
                "SOL-USDT",
                "--timeframe",
                "5m",
                "--days",
                "3",
                "--base-dir",
                "custom/path",
            ],
        ):
            result = main()

        assert result == 0
        # Vérifier que le repository a été créé avec le bon chemin
        mock_repo_class.assert_called_once_with(base_dir="custom/path")

        # Vérifier les arguments de save
        call_args = mock_repo.save.call_args
        assert call_args[0][0] == "SOL-USDT"
        assert call_args[0][1] == "5m"

    @patch("scripts.ingest_candles.KucoinMarketDataProvider")
    @patch("scripts.ingest_candles.CsvCandleRepository")
    def test_main_exception_handling(self, mock_repo_class, mock_provider_class):
        """Test la gestion des exceptions."""
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        # Simuler une exception
        mock_provider.get_ohlcv.side_effect = Exception("API Error")

        with patch("sys.argv", ["ingest_candles.py"]):
            result = main()

        # Devrait retourner 1 en cas d'erreur
        assert result == 1

    @patch("scripts.ingest_candles.KucoinMarketDataProvider")
    @patch("scripts.ingest_candles.CsvCandleRepository")
    def test_main_date_range_calculation(self, mock_repo_class, mock_provider_class):
        """Test que la plage de dates est correctement calculée."""
        mock_provider = MagicMock()
        mock_repo = MagicMock()
        mock_provider_class.return_value = mock_provider
        mock_repo_class.return_value = mock_repo

        base_time = datetime(2024, 1, 1, tzinfo=UTC)
        test_candles = [Candle(base_time, 100.0, 105.0, 95.0, 102.0, 1000.0)]
        mock_provider.get_ohlcv.return_value = test_candles

        with patch("sys.argv", ["ingest_candles.py", "--days", "14"]):
            result = main()

        assert result == 0

        # Vérifier que get_ohlcv a été appelé
        call_args = mock_provider.get_ohlcv.call_args
        start_date = call_args[0][2]
        end_date = call_args[0][3]

        # La différence devrait être d'environ 14 jours
        delta = end_date - start_date
        assert 13 <= delta.days <= 14
