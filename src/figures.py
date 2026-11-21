"""Construcción de las figuras Plotly."""

import pandas as pd
import plotly.graph_objects as go

from src.config import COLORES, COLORES_CASO, PAISES, TECNOLOGIAS

LAYOUT_BASE = dict(
    template="plotly_white",
    margin=dict(l=55, r=20, t=50, b=70),
    legend=dict(orientation="h", y=-0.12, yanchor="top", x=0),
    hovermode="x unified",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
    title=dict(x=0, y=0.97, yanchor="top", font=dict(size=15)),
)


def fig_paridad(df: pd.DataFrame, fc: pd.DataFrame) -> go.Figure:
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
    if not fc.empty:
        _add_proyeccion(fig, fc)
    fig.add_hline(y=0, line_width=1, line_color="#9aa5b1")
    fig.update_layout(**LAYOUT_BASE, yaxis_title="USD/MWh", bargap=0.3)
    fig.update_layout(title_text="Precio capturado frente a LCOE efectivo")
    return fig


def _add_proyeccion(fig: go.Figure, fc: pd.DataFrame) -> None:
    """Añade la proyección 2026-2028: banda del 80 % y líneas discontinuas."""
    fig.add_trace(go.Scatter(
        x=pd.concat([fc["fecha"], fc["fecha"][::-1]]),
        y=pd.concat([fc["capturado_sup"], fc["capturado_inf"][::-1]]),
        fill="toself", fillcolor="rgba(31, 78, 121, 0.12)", line=dict(width=0),
        name="Intervalo 80 % (proyección)", hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=fc["fecha"], y=fc["capturado_media"], name="Precio capturado (proyección)",
        line=dict(color=COLORES["capturado"], width=2, dash="dash"),
        hovertemplate="%{y:.1f} USD/MWh",
    ))
    fig.add_trace(go.Scatter(
        x=fc["fecha"], y=fc["lcoe_efectivo"], name="LCOE efectivo (proyección)",
        line=dict(color=COLORES["lcoe_efectivo"], width=2, dash="dash"),
        hovertemplate="%{y:.1f} USD/MWh",
    ))
    fig.add_vline(x=fc["fecha"].min(), line_width=1, line_dash="dot", line_color="#9aa5b1")


def fig_vertimiento(df: pd.DataFrame, fc: pd.DataFrame) -> go.Figure:
    """Tasa de vertimiento mensual, histórica y proyectada."""
    fig = go.Figure(go.Bar(
        x=df["fecha"], y=df["vertimiento"] * 100, name="Vertimiento",
        marker_color=COLORES["vertimiento"], hovertemplate="%{y:.1f} %",
    ))
    if not fc.empty:
        fig.add_trace(go.Bar(
            x=fc["fecha"], y=fc["vert_media"] * 100, name="Proyección",
            marker_color="rgba(127, 140, 141, 0.35)", hovertemplate="%{y:.1f} %",
        ))
    fig.update_layout(**LAYOUT_BASE, yaxis_title="% de la energía disponible", showlegend=False,
                      barmode="overlay")
    fig.update_layout(title_text="Tasa de vertimiento")
    return fig


def fig_panorama(anual: pd.DataFrame) -> go.Figure:
    """Margen de paridad anual de los 4 casos (2026: real parcial)."""
    fig = go.Figure()
    for (pais, tec), color in COLORES_CASO.items():
        a = anual[(anual["pais"] == pais) & (anual["tecnologia"] == tec)].sort_values("anio")
        etiquetas = [f"{x}*" if x == 2026 else str(x) for x in a["anio"]]
        fig.add_trace(go.Bar(
            x=etiquetas, y=a["margen"], name=f"{TECNOLOGIAS[tec]} · {PAISES[pais]}",
            marker_color=color, customdata=a["meses"],
            hovertemplate="%{y:+.1f} USD/MWh (%{customdata} meses)<extra>%{fullData.name}</extra>",
        ))
    fig.add_hline(y=0, line_width=1.5, line_color="#1c2733")
    fig.update_layout(**{**LAYOUT_BASE, "hovermode": "closest"}, barmode="group",
                      yaxis_title="Margen de paridad (USD/MWh)",
                      xaxis=dict(type="category", categoryorder="category ascending"))
    fig.update_layout(title_text="Margen de paridad por año: por encima de 0, el mercado paga el coste real")
    return fig
