"""Compara la proyección de 2026 con los datos reales de 2026 ya publicados.

Uso:
    python -m scripts.backtest_2026

Brasil: ONS publica constrained-off y CMO de 2026 con 1-2 meses de retraso.
Chile: precio del visor del Coordinador y reducciones ERV oficiales.
Escribe data/processed/real_2026.csv (meses de 2026 con dato real).
"""

import pandas as pd

from src.config import DATA_PROCESSED
from src.lcoe import LCOE_ANUAL
from src.sources import chile, ons
from src.sources.brasil_precio import pld_horario_usd


def brasil_2026(hasta: str = "2026-10") -> pd.DataFrame:
    precio = pld_horario_usd(range(2026, 2027))
    filas = []
    for tec in ["solar", "eolica"]:
        h = ons.horario(tec, "2026-01", hasta).merge(precio, on=["submercado", "hora"])
        h["mes"] = h["hora"].dt.to_period("M").dt.to_timestamp()
        h["ingreso"] = h["precio_usd"] * h["generacion"]
        g = h.groupby("mes")[["generacion", "vertido", "ingreso"]].sum()
        filas.append(pd.DataFrame({
            "fecha": g.index, "pais": "BR", "tecnologia": tec,
            "precio_capturado": (g["ingreso"] / g["generacion"]).values,
            "vertimiento": (g["vertido"] / (g["vertido"] + g["generacion"])).values,
            "generacion_mwh": g["generacion"].values,
        }))
    return pd.concat(filas, ignore_index=True)


def chile_2026(hasta: str = "2026-04") -> pd.DataFrame:
    """Chile 2026: precio del visor descargado y vertimiento oficial.

    Solo hasta abril: la API pública de generación del Coordinador deja de
    publicar el 13/05/2026, y sin generación no hay precio capturado.
    """
    c = chile.mensual("2026-01", hasta)
    return c.dropna(subset=["precio_capturado", "vertimiento"])[
        ["fecha", "pais", "tecnologia", "precio_capturado", "vertimiento", "generacion_mwh"]]


def main() -> None:
    real = pd.concat([brasil_2026(), chile_2026()], ignore_index=True)
    real.to_csv(DATA_PROCESSED / "real_2026.csv", index=False)
    fc = pd.read_csv(DATA_PROCESSED / "forecast.csv", parse_dates=["fecha"])
    m = real.merge(fc, on=["fecha", "pais", "tecnologia"])
    m["dentro_intervalo"] = m["precio_capturado"].between(m["capturado_inf"], m["capturado_sup"])
    resumen = m.groupby(["pais", "tecnologia"]).agg(
        meses=("fecha", "size"),
        capturado_real=("precio_capturado", "mean"),
        capturado_proy=("capturado_media", "mean"),
        vert_real=("vertimiento", "mean"),
        vert_proy=("vert_media", "mean"),
        pct_dentro_80=("dentro_intervalo", "mean"),
    )
    print(resumen.round(3))


if __name__ == "__main__":
    main()
