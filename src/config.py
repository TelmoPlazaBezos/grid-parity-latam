"""Constantes compartidas por toda la aplicación."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = ROOT / "data" / "processed"
MONTHLY_FILE = DATA_PROCESSED / "monthly.csv"

PAISES = {"BR": "Brasil", "CL": "Chile"}
TECNOLOGIAS = {"solar": "Solar PV", "eolica": "ONW"}

# Paleta: un color por serie, iguales en todos los gráficos.
COLORES = {
    "capturado": "#1f4e79",
    "lcoe_efectivo": "#c0504d",
    "lcoe": "#e6a5a3",
    "margen_pos": "rgba(46, 125, 50, 0.45)",
    "margen_neg": "rgba(192, 80, 77, 0.30)",
    "vertimiento": "#7f8c8d",
}

# Un color por caso en la vista comparativa: eólica en azules, solar en naranjas.
COLORES_CASO = {
    ("CL", "eolica"): "#1f4e79",
    ("BR", "eolica"): "#7fa7cf",
    ("CL", "solar"): "#c55a11",
    ("BR", "solar"): "#f4b183",
}
