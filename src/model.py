"""Proyección a 3 años del precio capturado, el vertimiento y el LCOE.

Método
------
- Precio capturado y vertimiento: modelos ETS (Holt-Winters en forma de
  espacio de estados) por país y tecnología, con error aditivo y
  estacionalidad anual cuando hay al menos 24 meses de datos.
- Validación: se entrena con 2022-2024 y se predice 2025. Para cada serie se
  comparan tres candidatos (ETS con tendencia amortiguada, ETS sin tendencia
  y estacional ingenuo) y se elige el más simple cuyo MAE en 2025 no supere
  en más de un 5 % al mejor (parsimonia: evita extrapolar tendencias que
  apenas mejoran el ajuste).
- Proyección final: se reentrena con 2022-2025 y se proyectan 36 meses
  (2026-2028) con intervalos de predicción del 80 %.
- LCOE: tendencia log-lineal sobre los valores anuales de IRENA.

Los resultados se precalculan con `python -m scripts.build_forecast` y la app
solo lee CSV (no necesita statsmodels en producción).
"""

import warnings
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.exponential_smoothing.ets import ETSModel

from src.lcoe import LCOE_ANUAL

HORIZONTE = 36
NIVEL_INTERVALO = 0.80
LIMITES = {"precio_capturado": (0.0, None), "vertimiento": (0.0, 0.95)}


# Ordenados de más simple a más complejo (importa para la regla de parsimonia).
CANDIDATOS = {
    "Estacional ingenuo": None,
    "ETS sin tendencia": dict(trend=None, damped_trend=False),
    "ETS con tendencia amortiguada": dict(trend="add", damped_trend=True),
}
TOLERANCIA = 0.05  # un modelo más simple se prefiere si su MAE está a <5 % del mejor


def _ajustar(serie: pd.Series, spec: dict):
    """Ajusta un ETS; con estacionalidad anual si hay 2 años completos de datos."""
    estacional = "add" if len(serie) >= 24 else None
    modelo = ETSModel(serie, error="add", seasonal=estacional,
                      seasonal_periods=12 if estacional else None, **spec)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return modelo.fit(disp=False, maxiter=2000)


def _ingenuo(train: pd.Series, n: int) -> np.ndarray:
    """Repite el mismo mes del último año disponible (o el último valor)."""
    if len(train) >= 12:
        return np.resize(train.iloc[-12:].values, n)
    return np.repeat(train.iloc[-1], n)


def _predecir(train: pd.Series, nombre: str, n: int) -> np.ndarray:
    spec = CANDIDATOS[nombre]
    if spec is None:
        return _ingenuo(train, n)
    return _ajustar(train, spec).forecast(n).values


def validar(serie: pd.Series, corte: str = "2024-12-01") -> Dict[str, float]:
    """MAE fuera de muestra (año siguiente al corte) de cada candidato.

    Devuelve el MAE de cada modelo y el nombre del ganador. Si el
    entrenamiento tiene menos de 12 meses no se puede validar y se usa
    el estacional ingenuo (repetir el último año) por prudencia.
    """
    train = serie[serie.index <= corte]
    test = serie[serie.index > corte]
    if len(train) < 12 or test.empty:
        return {"modelo": "Estacional ingenuo", "validado": False, "n_test": len(test)}
    maes = {nombre: float(np.mean(np.abs(_predecir(train, nombre, len(test)) - test.values)))
            for nombre in CANDIDATOS}
    mejor = min(maes.values())
    # Parsimonia: el más simple cuyo MAE no supere al mejor en más de TOLERANCIA.
    ganador = next(n for n in CANDIDATOS if maes[n] <= mejor * (1 + TOLERANCIA))
    return {"modelo": ganador, "validado": True, "n_test": len(test),
            "mae": maes[ganador], "mae_ingenuo": maes["Estacional ingenuo"],
            **{f"mae_{k}": v for k, v in maes.items()}}


def proyectar(serie: pd.Series, variable: str, modelo: str) -> pd.DataFrame:
    """Proyección a HORIZONTE meses con intervalo de predicción del 80 %."""
    fechas = pd.date_range(serie.index[-1] + pd.offsets.MonthBegin(1), periods=HORIZONTE, freq="MS")
    spec = CANDIDATOS[modelo]
    if spec is None:
        media = _ingenuo(serie, HORIZONTE)
        # Error típico del ingenuo estacional, creciente con los años de horizonte.
        sigma = (serie - serie.shift(12)).dropna().std()
        anios = np.ceil(np.arange(1, HORIZONTE + 1) / 12)
        z = 1.2816  # cuantil 90 % de la normal -> intervalo central del 80 %
        inf, sup = media - z * sigma * np.sqrt(anios), media + z * sigma * np.sqrt(anios)
    else:
        ajuste = _ajustar(serie, spec)
        resumen = ajuste.get_prediction(start=len(serie), end=len(serie) + HORIZONTE - 1) \
                        .summary_frame(alpha=1 - NIVEL_INTERVALO)
        media, inf, sup = resumen["mean"].values, resumen["pi_lower"].values, resumen["pi_upper"].values
    lo, hi = LIMITES[variable]
    out = pd.DataFrame({"fecha": fechas, "media": media, "inf": inf, "sup": sup})
    out[["media", "inf", "sup"]] = out[["media", "inf", "sup"]].clip(lower=lo, upper=hi)
    return out


def proyectar_lcoe(tecnologia: str, anios: Tuple[int, int] = (2026, 2028)) -> pd.Series:
    """LCOE anual proyectado con tendencia log-lineal sobre los datos de IRENA."""
    hist = pd.Series(LCOE_ANUAL[tecnologia])
    pendiente, origen = np.polyfit(hist.index.values, np.log(hist.values), 1)
    futuros = np.arange(anios[0], anios[1] + 1)
    return pd.Series(np.exp(origen + pendiente * futuros), index=futuros)
