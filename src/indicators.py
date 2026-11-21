"""Cálculo de los indicadores de paridad de red."""

import pandas as pd


def lcoe_efectivo(lcoe: pd.Series, vertimiento: pd.Series) -> pd.Series:
    """LCOE por MWh realmente vendido: LCOE / (1 - v).

    Args:
        lcoe: LCOE contable en USD/MWh.
        vertimiento: tasa de vertimiento en tanto por uno (0-1).
    """
    v = vertimiento.clip(lower=0, upper=0.95)  # evita dividir por ~0
    return lcoe / (1 - v)


def add_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Añade ratio de captura, LCOE efectivo y margen de paridad al dataset mensual.

    Espera las columnas: precio_base, precio_capturado, vertimiento, lcoe.
    """
    out = df.copy()
    out["ratio_captura"] = out["precio_capturado"] / out["precio_base"]
    out["lcoe_efectivo"] = lcoe_efectivo(out["lcoe"], out["vertimiento"])
    out["margen"] = out["precio_capturado"] - out["lcoe_efectivo"]
    return out
