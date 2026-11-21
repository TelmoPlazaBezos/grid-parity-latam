"""Constantes compartidas por toda la aplicación."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = ROOT / "data" / "processed"
MONTHLY_FILE = DATA_PROCESSED / "monthly.csv"

PAISES = {"BR": "Brasil", "CL": "Chile"}
TECNOLOGIAS = {"solar": "Solar FV", "eolica": "Eólica terrestre"}

# Paleta: un color por serie, iguales en todos los gráficos.
COLORES = {
    "capturado": "#1f4e79",
    "lcoe_efectivo": "#c0504d",
    "lcoe": "#e6a5a3",
    "margen_pos": "rgba(46, 125, 50, 0.18)",
    "margen_neg": "rgba(192, 80, 77, 0.18)",
    "vertimiento": "#7f8c8d",
}
