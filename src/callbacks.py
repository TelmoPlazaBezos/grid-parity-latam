"""Interactividad: un único callback que actualiza titular, KPIs y gráficos."""

from typing import Tuple

import pandas as pd
import plotly.graph_objects as go
from dash import Dash, Input, Output

from src.config import PAISES, TECNOLOGIAS
from src.figures import fig_paridad, fig_vertimiento


def register_callbacks(app: Dash, df: pd.DataFrame) -> None:
    """Registra los callbacks sobre el dataset ya cargado."""

    @app.callback(
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
    def actualizar(pais: str, tecnologia: str) -> Tuple[str, str, str, str, str, go.Figure, go.Figure]:
        sel = df[(df["pais"] == pais) & (df["tecnologia"] == tecnologia)].sort_values("fecha")
        ultimo = sel[sel["fecha"].dt.year == sel["fecha"].dt.year.max()]

        margen = ultimo["margen"].mean()
        vert = ultimo["vertimiento"].mean()
        captura = ultimo["ratio_captura"].mean()
        hay_paridad = margen > 0

        nombre = f"{TECNOLOGIAS[tecnologia]} en {PAISES[pais]}"
        titular = (f"{nombre}: el precio capturado cubre el LCOE efectivo"
                   if hay_paridad else
                   f"{nombre}: el precio capturado no cubre el LCOE efectivo")

        return (
            titular,
            f"{margen:+.1f}",
            f"{vert:.1%}",
            f"{captura:.0%}",
            "Sí" if hay_paridad else "No",
            fig_paridad(sel),
            fig_vertimiento(sel),
        )
