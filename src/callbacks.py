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


def _tabla_previsiones(prev: pd.DataFrame, pais: str) -> Optional[html.Table]:
    """Tabla de previsiones públicas de terceros para el país elegido."""
    if prev.empty:
        return None
    p = prev[prev["pais"] == pais]
    cabecera = html.Tr([html.Th(c) for c in ["Fuente", "Fecha", "Qué dice", "Frente al modelo"]])
    filas = [html.Tr([
        html.Td(html.A(r["fuente"], href=r["url"], target="_blank")),
        html.Td(r["fecha"]), html.Td(r["que_dice"]), html.Td(r["frente_al_modelo"]),
    ]) for _, r in p.iterrows()]
    return html.Table([html.Thead(cabecera), html.Tbody(filas)], className="tabla")


def _contraste_2026(real26: pd.DataFrame, fc: pd.DataFrame, pais: str, tecnologia: str) -> str:
    """Compara la proyección de 2026 con los meses de 2026 ya publicados."""
    r = _filtrar(real26, pais, tecnologia)
    if r.empty:
        return ("Aún no se han integrado datos reales de 2026 para este país; "
                "la tabla recoge previsiones públicas de terceros.")
    m = r.merge(_filtrar(fc, pais, tecnologia), on=["fecha", "pais", "tecnologia"])
    dentro = m["precio_capturado"].between(m["capturado_inf"], m["capturado_sup"]).mean()
    return (f"Contraste con lo real de 2026 ({len(m)} meses publicados): vertimiento real "
            f"{m['vertimiento'].mean():.1%} frente a {m['vert_media'].mean():.1%} proyectado; precio "
            f"capturado real {m['precio_capturado'].mean():.1f} frente a "
            f"{m['capturado_media'].mean():.1f} USD/MWh proyectado. {dentro:.0%} de los meses "
            "quedan dentro del intervalo del 80 %.")


def _titular_2026(anual_2026: pd.DataFrame, pais: str, tecnologia: str) -> str:
    """Segunda línea del titular con lo que dicen los meses reales de 2026."""
    if anual_2026.empty:
        return ""
    a = anual_2026[(anual_2026["pais"] == pais) & (anual_2026["tecnologia"] == tecnologia)]
    if a.empty:
        return ""
    r = a.iloc[0]
    estado = "mantiene la paridad" if r["margen"] > 0 else "sigue sin paridad"
    if 0 < r["margen"] < 5:
        estado = "queda al límite de la paridad"
    return (f"2026 (real, {int(r['meses'])} meses): {estado}, con un margen de "
            f"{r['margen']:+.1f} USD/MWh y un vertimiento del {r['vertimiento']:.0%}.")


def register_callbacks(app: Dash, df: pd.DataFrame, fc: pd.DataFrame, val: pd.DataFrame,
                       prev: pd.DataFrame, real26: pd.DataFrame,
                       anual_hist: pd.DataFrame, anual_2026: pd.DataFrame) -> None:
    """Registra los callbacks sobre los datos ya cargados."""

    @app.callback(
        Output("aviso", "children"),
        Output("titular", "children"),
        Output("titular-2026", "children"),
        Output("kpi-margen", "children"),
        Output("kpi-vert", "children"),
        Output("kpi-captura", "children"),
        Output("kpi-paridad", "children"),
        Output("kpi-proyeccion", "children"),
        Output("g-paridad", "figure"),
        Output("nota-modelo", "children"),
        Output("g-vertimiento", "figure"),
        Output("contraste-2026", "children"),
        Output("tabla-previsiones", "children"),
        Input("pais", "value"),
        Input("tecnologia", "value"),
    )
    def actualizar(pais: str, tecnologia: str) -> Tuple:
        sel = _filtrar(df, pais, tecnologia)
        sel_fc = _filtrar(fc, pais, tecnologia)
        a = _filtrar(anual_hist.rename(columns={"anio": "fecha"}), pais, tecnologia)
        ultimo = a.iloc[-1]
        anio = int(ultimo["fecha"])
        hay_paridad = ultimo["margen"] > 0

        nombre = f"{TECNOLOGIAS[tecnologia]} en {PAISES[pais]}"
        verbo = "cubre" if hay_paridad else "no cubre"
        titular = f"{nombre}: en {anio} el precio capturado {verbo} el LCOE efectivo"
        titular_2026 = _titular_2026(anual_2026, pais, tecnologia)

        if sel_fc.empty:
            proy = "–"
        else:
            m28 = sel_fc[sel_fc["fecha"].dt.year == sel_fc["fecha"].dt.year.max()]["margen"].mean()
            proy = f"{m28:+.1f}"

        return (
            _aviso(sel), titular, titular_2026,
            f"{ultimo['margen']:+.1f}", f"{ultimo['vertimiento']:.1%}",
            f"{ultimo['ratio_captura']:.0%}", "Sí" if hay_paridad else "No", proy,
            fig_paridad(sel, sel_fc), _nota_modelo(val, pais, tecnologia),
            fig_vertimiento(sel, sel_fc),
            _contraste_2026(real26, fc, pais, tecnologia),
            _tabla_previsiones(prev, pais),
        )
