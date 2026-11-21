"""LCOE anual por tecnología (USD/MWh, USD constantes).

PROVISIONAL: medias ponderadas mundiales de IRENA (Renewable Power Generation
Costs). Solar 2024-2025 según el informe de julio de 2026 (43 -> 44 USD/MWh).
El resto de valores está pendiente de verificar contra el informe y de
sustituir por valores de Brasil y Chile si IRENA los publica por país.
"""

LCOE_ANUAL = {
    # tecnologia: {anio: USD/MWh}
    "solar": {2022: 49.0, 2023: 44.0, 2024: 43.0, 2025: 44.0},
    "eolica": {2022: 33.0, 2023: 33.0, 2024: 34.0, 2025: 34.0},
}
FUENTE = "IRENA, media mundial (provisional)"

