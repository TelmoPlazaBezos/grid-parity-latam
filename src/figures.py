"""Construcción de las figuras Plotly."""

import pandas as pd
import plotly.graph_objects as go

from src.config import COLORES

LAYOUT_BASE = dict(
    template="plotly_white",
    margin=dict(l=55, r=20, t=70, b=40),
    legend=dict(orientation="h", y=1.02, yanchor="bottom", x=0),
    hovermode="x unified",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
    title=dict(x=0, y=0.97, yanchor="top", font=dict(size=15)),
)


def fig_paridad(df: pd.DataFrame) -> go.Figure:
    """Precio capturado frente a LCOE efectivo.

    Las barras de fondo muestran el margen de paridad de cada mes:
    verde si el precio capturado cubre el LCOE efectivo, rojo si no.
    """
    margen = df["margen"]
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["fecha"], y=margen, name="Margen de paridad",
        marker_color=[COLORES["margen_pos"] if m > 0 else COLORES["margen_neg"] for m in margen],
        hovertemplate="%{y:+.1f} USD/MWh",
    ))
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["lcoe_efectivo"], name="LCOE efectivo",
        line=dict(color=COLORES["lcoe_efectivo"], width=2),
        hovertemplate="%{y:.1f} USD/MWh",
    ))
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["lcoe"], name="LCOE contable",
        line=dict(color=COLORES["lcoe"], width=1.5, dash="dot"),
        hovertemplate="%{y:.1f} USD/MWh",
    ))
    fig.add_trace(go.Scatter(
        x=df["fecha"], y=df["precio_capturado"], name="Precio capturado",
        line=dict(color=COLORES["capturado"], width=2.5),
        hovertemplate="%{y:.1f} USD/MWh",
    ))
    fig.add_hline(y=0, line_width=1, line_color="#9aa5b1")
    fig.update_layout(**LAYOUT_BASE, yaxis_title="USD/MWh", bargap=0.3)
    fig.update_layout(title_text="Precio capturado frente a LCOE efectivo")
    return fig


def fig_vertimiento(df: pd.DataFrame) -> go.Figure:
    """Tasa de vertimiento mensual."""
    fig = go.Figure(go.Bar(
        x=df["fecha"], y=df["vertimiento"] * 100, name="Vertimiento",
        marker_color=COLORES["vertimiento"], hovertemplate="%{y:.1f} %",
    ))
    fig.update_layout(**LAYOUT_BASE, yaxis_title="% de la energía disponible", showlegend=False)
    fig.update_layout(title_text="Tasa de vertimiento")
    return fig
