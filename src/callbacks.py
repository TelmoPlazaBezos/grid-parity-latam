"""Interactividad: un único callback que actualiza aviso, titular, KPIs y gráficos."""

from typing import Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, html

from src.config import PAISES, TECNOLOGIAS
from src.figures import fig_paridad, fig_vertimiento


def _filtrar(df: pd.DataFrame, pais: str, tecnologia: str) -> pd.DataFrame:
    if df.empty:
        return df
    return df[(df["pais"] == pais) & (df["tecnologia"] == tecnologia)].sort_values("fecha")


def _aviso(sel: pd.DataFrame) -> Optional[html.Div]:
    faltan = int(sel["precio_capturado"].isna().sum())
    if (sel["fuente"] == "demo").any():
        return html.Div("Datos de prueba sintéticos para este país: aún no son datos reales.",
                        className="aviso")
    if faltan:
        return html.Div(f"Faltan precios de {faltan} meses: los indicadores de precio y margen "
                        "usan solo los meses disponibles.", className="aviso")
    return None


def _nota_modelo(val: pd.DataFrame, pais: str, tecnologia: str) -> str:
    """Texto con el modelo elegido y su error fuera de muestra en 2025."""
    if val.empty:
        return ""
    v = val[(val["pais"] == pais) & (val["tecnologia"] == tecnologia)
            & (val["variable"] == "precio_capturado")]
    if v.empty:
        return ""
    v = v.iloc[0]
    base = "Proyección 2026-2028 con intervalo del 80 %. "
    if not bool(v["validado"]):
        return base + ("Sin validación fuera de muestra (la serie empieza en abril de 2024: ONS no "
                       "publica vertimiento solar antes), así que se repite el perfil de 2025.")
    return base + (f"Modelo del precio capturado: {v['modelo']} · MAE en 2025: "
                   f"{v['mae']:.1f} USD/MWh (referencia ingenua: {v['mae_ingenuo']:.1f}).")


def register_callbacks(app: Dash, df: pd.DataFrame, fc: pd.DataFrame, val: pd.DataFrame) -> None:
    """Registra los callbacks sobre los datos ya cargados."""

    @app.callback(
        Output("aviso", "children"),
        Output("titular", "children"),
        Output("kpi-margen", "children"),
        Output("kpi-vert", "children"),
        Output("kpi-captura", "children"),
        Output("kpi-paridad", "children"),
        Output("kpi-proyeccion", "children"),
        Output("g-paridad", "figure"),
        Output("nota-modelo", "children"),
        Output("g-vertimiento", "figure"),
        Input("pais", "value"),
        Input("tecnologia", "value"),
    )
    def actualizar(pais: str, tecnologia: str) -> Tuple:
        sel = _filtrar(df, pais, tecnologia)
        sel_fc = _filtrar(fc, pais, tecnologia)
        anio = int(sel["fecha"].dt.year.max())
        ultimo = sel[sel["fecha"].dt.year == anio]

        margen = ultimo["margen"].mean()
        vert = ultimo["vertimiento"].mean()
        captura = ultimo["ratio_captura"].mean()
        hay_paridad = margen > 0

        nombre = f"{TECNOLOGIAS[tecnologia]} en {PAISES[pais]}"
        verbo = "cubre" if hay_paridad else "no cubre"
        titular = f"{nombre}: en {anio} el precio capturado {verbo} el LCOE efectivo"

        if sel_fc.empty:
            proy = "–"
        else:
            m28 = sel_fc[sel_fc["fecha"].dt.year == sel_fc["fecha"].dt.year.max()]["margen"].mean()
            proy = f"{m28:+.1f}"

        return (
            _aviso(sel), titular,
            f"{margen:+.1f}", f"{vert:.1%}", f"{captura:.0%}",
            "Sí" if hay_paridad else "No", proy,
            fig_paridad(sel, sel_fc), _nota_modelo(val, pais, tecnologia),
            fig_vertimiento(sel, sel_fc),
        )
