"""Estructura visual de la aplicación."""

from dash import dcc, html

from src.config import PAISES, TECNOLOGIAS


def kpi(id_: str, etiqueta: str) -> html.Div:
    """Tarjeta de indicador; el valor lo rellena un callback."""
    return html.Div(className="kpi", children=[
        html.Div(etiqueta, className="kpi-label"),
        html.Div("–", id=id_, className="kpi-value"),
    ])


def build_layout() -> html.Div:
    """Devuelve el layout completo."""

    return html.Div(className="page", children=[
        html.Header(className="header", children=[
            html.H1("Grid Parity LatAm"),
            html.P("¿Siguen siendo rentables la solar y la eólica en Brasil y Chile "
                   "cuando se descuenta la energía vertida?"),
        ]),
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
        html.Div(className="kpis", children=[
            kpi("kpi-margen", "Margen medio último año (USD/MWh)"),
            kpi("kpi-vert", "Vertimiento último año"),
            kpi("kpi-captura", "Ratio de captura"),
            kpi("kpi-paridad", "¿Paridad de red?"),
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
            "Nacional, IRENA (LCOE provisional: media mundial). Telmo Plaza Bezos · DAVD 2026-27.",
        ]),
    ])
