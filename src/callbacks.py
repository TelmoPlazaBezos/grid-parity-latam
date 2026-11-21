"""Interactividad: un único callback que actualiza titular, KPIs y gráficos."""

from typing import Tuple

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output, html

from src.config import PAISES, TECNOLOGIAS
from src.figures import fig_paridad, fig_vertimiento


def register_callbacks(app: Dash, df: pd.DataFrame) -> None:
    """Registra los callbacks sobre el dataset ya cargado."""

    @app.callback(
        Output("aviso", "children"),
        Output("titular", "children"),
        Output("kpi-margen", "children"),
        Output("kpi-vert", "children"),
        Output("kpi-captura", "children"),
        Output("kpi-paridad", "children"),
        Output("g-paridad", "figure"),
        Output("g-vertimiento", "figure"),
        Input("pais", "value"),
        Input("tecnologia", "value"),
    )
    def actualizar(pais: str, tecnologia: str) -> Tuple[object, str, str, str, str, str, go.Figure, go.Figure]:
        sel = df[(df["pais"] == pais) & (df["tecnologia"] == tecnologia)].sort_values("fecha")
        ultimo = sel[sel["fecha"].dt.year == sel["fecha"].dt.year.max()]

        margen = ultimo["margen"].mean()
        vert = ultimo["vertimiento"].mean()
        captura = ultimo["ratio_captura"].mean()
        hay_paridad = margen > 0

        aviso = (html.Div("Datos de prueba sintéticos para este país: aún no son datos reales.",
                          className="aviso") if (sel["fuente"] == "demo").any() else None)
        anio = int(ultimo["fecha"].dt.year.max())

        nombre = f"{TECNOLOGIAS[tecnologia]} en {PAISES[pais]}"
        titular = (f"{nombre}: en {anio} el precio capturado cubre el LCOE efectivo"
                   if hay_paridad else
                   f"{nombre}: en {anio} el precio capturado no cubre el LCOE efectivo")

        return (
            aviso,
            titular,
            f"{margen:+.1f}",
            f"{vert:.1%}",
            f"{captura:.0%}",
            "Sí" if hay_paridad else "No",
            fig_paridad(sel),
            fig_vertimiento(sel),
        )
