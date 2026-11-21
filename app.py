"""Punto de entrada de la app Grid Parity LatAm (local y Render)."""

from dash import Dash

from src.callbacks import register_callbacks
from src.data import (load_forecast, load_monthly, load_previsiones, load_real_2026,
                      load_validacion)
from src.layout import build_layout

df = load_monthly()
fc = load_forecast()
val = load_validacion()
prev = load_previsiones()
real26 = load_real_2026()

app = Dash(__name__, title="Grid Parity LatAm")
server = app.server  # gunicorn lo usa en Render: `gunicorn app:server`

app.layout = build_layout()
register_callbacks(app, df, fc, val, prev, real26)

if __name__ == "__main__":
    app.run(debug=True)
