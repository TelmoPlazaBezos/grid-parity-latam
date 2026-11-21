"""Punto de entrada de la app Grid Parity LatAm (local y Render)."""

import pandas as pd
from dash import Dash

from src.annual import anual
from src.callbacks import register_callbacks
from src.data import (load_forecast, load_monthly, load_previsiones, load_real_2026,
                      load_validacion)
from src.figures import fig_panorama
from src.layout import build_layout
from src.lcoe import LCOE_ANUAL

df = load_monthly()
fc = load_forecast()
val = load_validacion()
prev = load_previsiones()
real26 = load_real_2026()

# LCOE por año: IRENA hasta 2025 y, desde 2026, el proyectado en forecast.csv.
lcoe = {t: dict(v) for t, v in LCOE_ANUAL.items()}
if not fc.empty:
    for (t, a), x in fc.assign(anio=fc["fecha"].dt.year).groupby(["tecnologia", "anio"])["lcoe"]:
        lcoe[t].setdefault(a, float(x.iloc[0]))
anual_hist = anual(df, lcoe)
anual_2026 = anual(real26, lcoe) if not real26.empty else pd.DataFrame()

app = Dash(__name__, title="Grid Parity LatAm")
server = app.server  # gunicorn lo usa en Render: `gunicorn app:server`

app.layout = build_layout(fig_panorama(pd.concat([anual_hist, anual_2026], ignore_index=True)))
register_callbacks(app, df, fc, val, prev, real26, anual_hist, anual_2026)

if __name__ == "__main__":
    app.run(debug=True)
