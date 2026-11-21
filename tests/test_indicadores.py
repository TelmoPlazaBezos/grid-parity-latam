"""Tests de los cálculos centrales: LCOE efectivo, margen y agregación anual."""

import numpy as np
import pandas as pd
import pytest

from src.annual import anual
from src.indicators import add_indicadores, lcoe_efectivo


def test_lcoe_efectivo_sin_vertimiento_es_el_lcoe():
    assert lcoe_efectivo(pd.Series([40.0]), pd.Series([0.0])).iloc[0] == 40.0


def test_lcoe_efectivo_con_20_por_ciento_vertido():
    # Si se vierte el 20 %, cada MWh vendido cuesta LCOE / 0,8.
    assert lcoe_efectivo(pd.Series([40.0]), pd.Series([0.2])).iloc[0] == pytest.approx(50.0)


def test_lcoe_efectivo_acota_vertimientos_extremos():
    # Un vertimiento del 100 % no debe dividir por cero.
    assert np.isfinite(lcoe_efectivo(pd.Series([40.0]), pd.Series([1.0])).iloc[0])


def test_margen_y_ratio_de_captura():
    df = pd.DataFrame({"precio_base": [60.0], "precio_capturado": [30.0],
                       "vertimiento": [0.25], "lcoe": [45.0]})
    out = add_indicadores(df).iloc[0]
    assert out["ratio_captura"] == pytest.approx(0.5)
    assert out["lcoe_efectivo"] == pytest.approx(60.0)
    assert out["margen"] == pytest.approx(-30.0)


def test_anual_pondera_por_energia_y_no_por_mes():
    # Mes 1: mucha energía a 10 USD/MWh; mes 2: poca energía a 100 USD/MWh.
    df = pd.DataFrame({
        "fecha": pd.to_datetime(["2025-01-01", "2025-02-01"]),
        "pais": "CL", "tecnologia": "solar",
        "precio_base": [50.0, 50.0], "precio_capturado": [10.0, 100.0],
        "vertimiento": [0.0, 0.0], "generacion_mwh": [900.0, 100.0],
    })
    a = anual(df, {"solar": {2025: 40.0}}).iloc[0]
    assert a["precio_capturado"] == pytest.approx(19.0)  # (10*900 + 100*100) / 1000
    assert a["margen"] == pytest.approx(19.0 - 40.0)
