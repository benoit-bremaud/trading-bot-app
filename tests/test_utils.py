"""Tests pour le module utils."""


def test_utils_module_exists():
    """Test que le module utils existe et peut être importé."""
    from trading_bot import utils

    assert utils is not None


def test_utils_module_is_empty():
    """Test que le module utils est actuellement vide."""
    from trading_bot import utils

    # Le fichier utils.py est vide, donc il ne devrait pas avoir
    # d'attributs publics
    public_attrs = [attr for attr in dir(utils) if not attr.startswith("_")]

    # On s'attend à ce qu'il n'y ait pas d'attributs publics définis
    assert len(public_attrs) == 0, f"Attributs publics trouvés: {public_attrs}"
