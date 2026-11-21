"""Precalcula proyecciones y métricas de validación para la app.

Uso (desde la raíz del repo, después de build_dataset):
    python -m scripts.build_forecast

Escribe:
    data/processed/forecast.csv    proyección mensual 2026-2028 con intervalos
    data/processed/validacion.csv  MAE 2025 del modelo frente a la referencia
"""

import pandas as pd

from src.config import DATA_PROCESSED
from src.data import load_monthly
from src.indicators import lcoe_efectivo
from src.model import proyectar, proyectar_lcoe, validar

VARIABLES = ["precio_capturado", "vertimiento"]


def main() -> None:
    df = load_monthly()
    proyecciones, metricas = [], []
    for (pais, tec), g in df.groupby(["pais", "tecnologia"]):
        g = g.set_index("fecha").sort_index().asfreq("MS")
        series = {}
        for var in VARIABLES:
            s = g[var].interpolate(limit=2).dropna()
            m = validar(s)
            metricas.append({"pais": pais, "tecnologia": tec, "variable": var, **m})
            series[var] = proyectar(s, var, m["modelo"])

        p = series["precio_capturado"].rename(columns=lambda c: f"capturado_{c}" if c != "fecha" else c)
        v = series["vertimiento"].rename(columns=lambda c: f"vert_{c}" if c != "fecha" else c)
        out = p.merge(v, on="fecha")
        out["lcoe"] = out["fecha"].dt.year.map(proyectar_lcoe(tec))
        out["lcoe_efectivo"] = lcoe_efectivo(out["lcoe"], out["vert_media"])
        out["margen"] = out["capturado_media"] - out["lcoe_efectivo"]
        out["pais"], out["tecnologia"] = pais, tec
        proyecciones.append(out)

    fc = pd.concat(proyecciones, ignore_index=True)
    num = fc.select_dtypes("number").columns
    fc[num] = fc[num].round(4)
    val = pd.DataFrame(metricas).round(4)
    fc.to_csv(DATA_PROCESSED / "forecast.csv", index=False)
    val.to_csv(DATA_PROCESSED / "validacion.csv", index=False)
    print(val.to_string(index=False))
    resumen = fc.assign(anio=fc["fecha"].dt.year).groupby(["pais", "tecnologia", "anio"])[
        ["capturado_media", "vert_media", "lcoe_efectivo", "margen"]].mean()
    print(resumen.round(2))


if __name__ == "__main__":
    main()
