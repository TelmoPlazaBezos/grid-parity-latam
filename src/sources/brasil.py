"""Brasil · indicadores mensuales por tecnología.

Cruza generación y vertimiento horarios (ONS) con el precio horario en USD
por submercado:
- precio capturado = sum(precio x generación) / sum(generación)
- precio base      = media simple del precio horario, ponderada por la
                     generación total de cada submercado en el mes
- vertimiento      = vertido / (generado + vertido)
"""

import pandas as pd

from src.sources import ons
from src.sources.brasil_precio import pld_horario_usd


def mensual() -> pd.DataFrame:
    precio = pld_horario_usd()
    partes = []
    for tec in ["solar", "eolica"]:
        h = ons.horario(tec).merge(precio, on=["submercado", "hora"], how="inner")
        h["mes"] = h["hora"].dt.to_period("M").dt.to_timestamp()
        h["ingreso"] = h["precio_usd"] * h["generacion"]
        g = h.groupby("mes").agg(generacion=("generacion", "sum"),
                                 vertido=("vertido", "sum"),
                                 ingreso=("ingreso", "sum"))
        # Precio base: media horaria de cada submercado, ponderada por su peso en la tecnología.
        base_sub = (h.groupby(["mes", "submercado"])
                     .agg(p=("precio_usd", "mean"), w=("generacion", "sum")).reset_index())
        base = base_sub.groupby("mes").apply(
            lambda x: (x["p"] * x["w"]).sum() / x["w"].sum(), include_groups=False)
        partes.append(pd.DataFrame({
            "fecha": g.index, "pais": "BR", "tecnologia": tec,
            "precio_base": base.reindex(g.index).values,
            "precio_capturado": (g["ingreso"] / g["generacion"]).values,
            "vertimiento": (g["vertido"] / (g["vertido"] + g["generacion"])).values,
            "generacion_mwh": g["generacion"].values,
        }))
    return pd.concat(partes, ignore_index=True)
