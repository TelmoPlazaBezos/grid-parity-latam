"""Carga del dataset mensual consolidado.

La app solo lee `data/processed/monthly.csv`; nunca descarga datos al arrancar
(Render debe arrancar rápido). Las descargas de CCEE, ONS, PTAX y Coordinador
se añadirán en este módulo y escribirán ese mismo CSV.

Mientras tanto, `build_demo_dataset` genera DATOS DE PRUEBA sintéticos con la
misma estructura, marcados con `fuente = "demo"`. No son datos reales.
"""

import numpy as np
import pandas as pd

from src.config import DATA_PROCESSED, MONTHLY_FILE, PAISES, TECNOLOGIAS
from src.indicators import add_indicadores

COLUMNAS = [
    "fecha", "pais", "tecnologia", "precio_base", "precio_capturado",
    "vertimiento", "lcoe", "fuente",
]


def build_demo_dataset(seed: int = 42) -> pd.DataFrame:
    """Genera un dataset sintético 2022-2025 con la estructura final. SOLO PRUEBAS."""
    rng = np.random.default_rng(seed)
    fechas = pd.date_range("2022-01-01", "2025-12-01", freq="MS")
    n = len(fechas)
    t = np.arange(n)
    estacional = np.sin(2 * np.pi * (fechas.month - 1) / 12)
    filas = []
    for pais in PAISES:
        base = (45 if pais == "BR" else 60) + 10 * estacional + rng.normal(0, 4, n)
        for tec in TECNOLOGIAS:
            castigo = 0.55 if tec == "solar" else 0.85
            capturado = base * (castigo - 0.004 * t) + rng.normal(0, 2, n)
            vert = np.clip(0.03 + 0.004 * t + rng.normal(0, 0.01, n), 0, 0.6)
            lcoe = (42 if tec == "solar" else 38) * np.ones(n)
            filas.append(pd.DataFrame({
                "fecha": fechas, "pais": pais, "tecnologia": tec,
                "precio_base": base.round(2), "precio_capturado": capturado.round(2),
                "vertimiento": vert.round(4), "lcoe": lcoe, "fuente": "demo",
            }))
    return pd.concat(filas, ignore_index=True)[COLUMNAS]


def load_monthly() -> pd.DataFrame:
    """Lee el dataset mensual y le añade los indicadores derivados."""
    if MONTHLY_FILE.exists():
        df = pd.read_csv(MONTHLY_FILE, parse_dates=["fecha"])
    else:
        df = build_demo_dataset()
    return add_indicadores(df)


def load_forecast() -> pd.DataFrame:
    """Proyecciones precalculadas (vacío si aún no existen)."""
    ruta = DATA_PROCESSED / "forecast.csv"
    return pd.read_csv(ruta, parse_dates=["fecha"]) if ruta.exists() else pd.DataFrame()


def load_validacion() -> pd.DataFrame:
    """Métricas de validación 2025 por serie (vacío si aún no existen)."""
    ruta = DATA_PROCESSED / "validacion.csv"
    return pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()


if __name__ == "__main__":
    MONTHLY_FILE.parent.mkdir(parents=True, exist_ok=True)
    build_demo_dataset().to_csv(MONTHLY_FILE, index=False)
    print(f"Dataset de prueba escrito en {MONTHLY_FILE}")
