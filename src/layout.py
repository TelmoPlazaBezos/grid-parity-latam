"""Estructura visual de la aplicación."""

import plotly.graph_objects as go
from dash import dcc, html

from src.config import PAISES, TECNOLOGIAS


def kpi(id_: str, etiqueta: str) -> html.Div:
    """Tarjeta de indicador; el valor lo rellena un callback."""
    return html.Div(className="kpi", children=[
        html.Div(etiqueta, className="kpi-label"),
        html.Div("–", id=id_, className="kpi-value"),
    ])


def build_layout(panorama: go.Figure) -> html.Div:
    """Devuelve el layout completo; la vista comparativa es estática."""

    return html.Div(className="page", children=[
        html.Header(className="header", children=[
            html.H1("Grid Parity LatAm"),
            html.P("¿Siguen siendo rentables la solar y la eólica en Brasil y Chile "
                   "cuando se descuenta la energía vertida?"),
        ]),
        html.H3("Panorama: los cuatro casos de un vistazo", className="seccion"),
        dcc.Graph(id="g-panorama", figure=panorama, config={"displayModeBar": False}),
        html.P("* 2026 con los meses reales ya publicados: Brasil enero-octubre, Chile enero-abril. "
               "LCOE de 2026 proyectado con la tendencia de IRENA.", className="nota"),
        html.H3("Detalle por país y tecnología", className="seccion"),
        html.Div(className="controls", children=[
            dcc.RadioItems(
                id="pais", value="BR", inline=True, className="radio",
                options=[{"label": v, "value": k} for k, v in PAISES.items()],
            ),
            dcc.RadioItems(
                id="tecnologia", value="solar", inline=True, className="radio",
                options=[{"label": v, "value": k} for k, v in TECNOLOGIAS.items()],
            ),
        ]),
        html.Div(id="aviso"),
        html.H2(id="titular", className="titular"),
        html.P(id="titular-2026", className="subtitular"),
        html.Div(className="kpis", children=[
            kpi("kpi-margen", "Margen 2025 (USD/MWh)"),
            kpi("kpi-vert", "Vertimiento 2025"),
            kpi("kpi-captura", "Ratio de captura 2025"),
            kpi("kpi-paridad", "¿Paridad en 2025?"),
            kpi("kpi-proyeccion", "Margen proyectado 2028 (USD/MWh)"),
        ]),
        dcc.Graph(id="g-paridad", config={"displayModeBar": False}),
        html.P(id="nota-modelo", className="nota"),
        dcc.Graph(id="g-vertimiento", config={"displayModeBar": False}),
        html.H3("Segunda opinión: ¿qué dicen otros?", className="seccion"),
        html.P(id="contraste-2026", className="nota"),
        html.Div(id="tabla-previsiones"),
        html.Footer(className="footer", children=[
            "Fuentes: CCEE, ONS, Banco Central do Brasil, Coordinador Eléctrico "
            "Nacional, IRENA (LCOE: media mundial ponderada). Telmo Plaza Bezos · DAVD 2026-27.",
        ]),
    ])
