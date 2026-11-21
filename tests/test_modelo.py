"""Tests de la selección de modelo y de la proyección."""

import numpy as np
import pandas as pd

from src.model import HORIZONTE, proyectar, validar


def _serie_estacional(n: int = 48, ruido: float = 1.0) -> pd.Series:
    fechas = pd.date_range("2022-01-01", periods=n, freq="MS")
    rng = np.random.default_rng(0)
    valores = 50 + 10 * np.sin(2 * np.pi * np.arange(n) / 12) + rng.normal(0, ruido, n)
    return pd.Series(valores, index=fechas)


def test_validar_elige_un_candidato_conocido():
    m = validar(_serie_estacional())
    assert m["validado"]
    assert m["modelo"] in {"Estacional ingenuo", "ETS sin tendencia", "ETS con tendencia amortiguada"}
    assert m["mae"] <= m["mae_ingenuo"] * 1.05 + 1e-9


def test_serie_corta_no_se_valida_y_usa_el_ingenuo():
    m = validar(_serie_estacional(n=20))
    assert not m["validado"]
    assert m["modelo"] == "Estacional ingenuo"


def test_proyeccion_tiene_horizonte_y_respeta_limites():
    s = _serie_estacional() / 100  # como un vertimiento entre 0 y 1
    p = proyectar(s, "vertimiento", "ETS sin tendencia")
    assert len(p) == HORIZONTE
    assert (p["inf"] >= 0).all() and (p["sup"] <= 0.95).all()
    assert (p["inf"] <= p["media"]).all() and (p["media"] <= p["sup"]).all()
