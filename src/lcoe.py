"""LCOE anual por tecnología (USD/MWh, USD constantes).

Medias ponderadas mundiales de IRENA (Renewable Power Generation Costs):
- 2022: solar 49, eólica 33 (informe 2022, ago 2023)
- 2023: solar 44, eólica 33 (informe 2023, sep 2024)
- 2024: solar 43, eólica 34 (informe 2024, jul 2025)
- 2025: solar 44, eólica 33 (informe 2025, jul 2026)
Todos verificados en los informes o en sus notas de prensa.
Mejora pendiente: IRENA publica valores por país para Brasil (eólica).
"""

LCOE_ANUAL = {
    # tecnologia: {anio: USD/MWh}
    "solar": {2022: 49.0, 2023: 44.0, 2024: 43.0, 2025: 44.0},
    "eolica": {2022: 33.0, 2023: 33.0, 2024: 34.0, 2025: 33.0},
}
FUENTE = "IRENA, media mundial ponderada"

