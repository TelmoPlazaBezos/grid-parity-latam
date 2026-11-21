"""Construye data/processed/monthly.csv, el único archivo que lee la app.

Uso (desde la raíz del repo):
    python -m scripts.build_dataset

Brasil: datos reales (ONS, CMO/PLD, PTAX).
Chile:  datos de prueba hasta integrar el Coordinador Eléctrico Nacional.
"""

import pandas as pd

from src.config import MONTHLY_FILE
from src.data import COLUMNAS, build_demo_dataset
from src.lcoe import LCOE_ANUAL
from src.sources import brasil


def main() -> None:
    br = brasil.mensual()
    br["lcoe"] = br.apply(lambda r: LCOE_ANUAL[r["tecnologia"]][r["fecha"].year], axis=1)
    br["fuente"] = "real"

    cl = build_demo_dataset()
    cl = cl[cl["pais"] == "CL"]

    out = pd.concat([br[COLUMNAS], cl[COLUMNAS]], ignore_index=True)
    out = out.sort_values(["pais", "tecnologia", "fecha"])
    num = ["precio_base", "precio_capturado", "lcoe"]
    out[num] = out[num].round(2)
    out["vertimiento"] = out["vertimiento"].round(4)
    MONTHLY_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(MONTHLY_FILE, index=False)
    print(f"{len(out)} filas escritas en {MONTHLY_FILE}")
    print(out.groupby(["pais", "tecnologia", "fuente"]).size())


if __name__ == "__main__":
    main()
