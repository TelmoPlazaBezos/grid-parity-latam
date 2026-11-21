"""Punto de entrada de la app Grid Parity LatAm (local y Render)."""

from dash import Dash

from src.callbacks import register_callbacks
from src.data import load_monthly
from src.layout import build_layout

df = load_monthly()

app = Dash(__name__, title="Grid Parity LatAm")
server = app.server  # gunicorn lo usa en Render: `gunicorn app:server`

app.layout = build_layout()
register_callbacks(app, df)

if __name__ == "__main__":
    app.run(debug=True)
