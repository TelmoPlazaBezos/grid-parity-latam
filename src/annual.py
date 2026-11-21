"""Agregación anual ponderada por energía.

Un mes con poca generación no debe pesar lo mismo que uno con mucha:
- precio capturado anual = ingresos / energía vendida
- vertimiento anual      = energía vertida / energía disponible
- margen anual           = precio capturado - LCOE / (1 - vertimiento)
"""

from typing import Dict

import pandas as pd

from src.indicators import lcoe_efectivo


def anual(df: pd.DataFrame, lcoe_por_anio: Dict[str, Dict[int, float]]) -> pd.DataFrame:
    """Indicadores anuales por país y tecnología a partir del dataset mensual.

    Args:
        df: columnas fecha, pais, tecnologia, precio_capturado, vertimiento,
            generacion_mwh (y opcionalmente precio_base).
        lcoe_por_anio: {tecnologia: {anio: USD/MWh}}.
    """
    d = df.dropna(subset=["precio_capturado", "vertimiento", "generacion_mwh"]).copy()
    d["anio"] = d["fecha"].dt.year
    d["ingreso"] = d["precio_capturado"] * d["generacion_mwh"]
    d["vertido"] = d["vertimiento"] / (1 - d["vertimiento"]) * d["generacion_mwh"]
    if "precio_base" in d:
        d["base_x_gen"] = d["precio_base"] * d["generacion_mwh"]
    else:
        d["base_x_gen"] = float("nan")
    g = d.groupby(["pais", "tecnologia", "anio"], as_index=False).agg(
        meses=("fecha", "size"), generacion=("generacion_mwh", "sum"),
        ingreso=("ingreso", "sum"), vertido=("vertido", "sum"),
        base_x_gen=("base_x_gen", lambda x: x.sum(min_count=1)))
    g["precio_capturado"] = g["ingreso"] / g["generacion"]
    g["vertimiento"] = g["vertido"] / (g["vertido"] + g["generacion"])
    g["ratio_captura"] = g["precio_capturado"] / (g["base_x_gen"] / g["generacion"])
    g["lcoe"] = [lcoe_por_anio[t].get(a, float("nan")) for t, a in zip(g["tecnologia"], g["anio"])]
    g["lcoe_efectivo"] = lcoe_efectivo(g["lcoe"], g["vertimiento"])
    g["margen"] = g["precio_capturado"] - g["lcoe_efectivo"]
    return g.drop(columns=["ingreso", "vertido", "base_x_gen"])
