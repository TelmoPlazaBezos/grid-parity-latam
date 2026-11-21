"""Estructura visual de la aplicación."""

from dash import dcc, html

from src.config import PAISES, TECNOLOGIAS


def kpi(id_: str, etiqueta: str) -> html.Div:
    """Tarjeta de indicador; el valor lo rellena un callback."""
    return html.Div(className="kpi", children=[
        html.Div(etiqueta, className="kpi-label"),
        html.Div("–", id=id_, className="kpi-value"),
    ])


def build_layout(es_demo: bool) -> html.Div:
    """Devuelve el layout completo."""
    aviso = html.Div(
        "Datos de prueba sintéticos: la app aún no usa datos reales.",
        className="aviso",
    ) if es_demo else None

    return html.Div(className="page", children=[
        html.Header(className="header", children=[
            html.H1("Grid Parity LatAm"),
            html.P("¿Siguen siendo rentables la solar y la eólica en Brasil y Chile "
                   "cuando se descuenta la energía vertida?"),
        ]),
        aviso,
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
        html.H2(id="titular", className="titular"),
        html.Div(className="kpis", children=[
            kpi("kpi-margen", "Margen último año (USD/MWh)"),
            kpi("kpi-vert", "Vertimiento último año"),
            kpi("kpi-captura", "Ratio de captura"),
            kpi("kpi-paridad", "¿Paridad de red?"),
        ]),
        dcc.Graph(id="g-paridad", config={"displayModeBar": False}),
        dcc.Graph(id="g-vertimiento", config={"displayModeBar": False}),
        html.Footer(className="footer", children=[
            "Fuentes: CCEE, ONS, Banco Central do Brasil, Coordinador Eléctrico "
            "Nacional, IRENA. Telmo Plaza Bezos · DAVD 2026-27.",
        ]),
    ])
