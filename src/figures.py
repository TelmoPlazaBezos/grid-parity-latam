"""Construcción de las figuras Plotly."""

import pandas as pd
import plotly.graph_objects as go

from src.config import COLORES

LAYOUT_BASE = dict(
    template="plotly_white",
    margin=dict(l=50, r=20, t=40, b=40),
    legend=dict(orientation="h", y=1.08, x=0),
    hovermode="x unified",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
)


def fig_paridad(df: pd.DataFrame) -> go.Figure:
    """Precio capturado frente a LCOE efectivo, con la brecha sombreada."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["lcoe_efectivo"], name="LCOE efectivo",
        line=dict(color=COLORES["lcoe_efectivo"], width=2),
    ))
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["precio_capturado"], name="Precio capturado",
        line=dict(color=COLORES["capturado"], width=2.5),
        fill="tonexty", fillcolor=COLORES["margen_neg"],
    ))
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["lcoe"], name="LCOE contable",
        line=dict(color=COLORES["lcoe"], width=1.5, dash="dot"),
    ))
    fig.update_layout(**LAYOUT_BASE, yaxis_title="USD/MWh",
                      title="Precio capturado frente a LCOE efectivo")
    return fig


def fig_vertimiento(df: pd.DataFrame) -> go.Figure:
    """Tasa de vertimiento mensual."""
    fig = go.Figure(go.Bar(
        x=df["fecha"], y=df["vertimiento"] * 100, name="Vertimiento",
        marker_color=COLORES["vertimiento"],
    ))
    fig.update_layout(**LAYOUT_BASE, yaxis_title="% de la energía disponible",
                      title="Tasa de vertimiento", showlegend=False)
    return fig
