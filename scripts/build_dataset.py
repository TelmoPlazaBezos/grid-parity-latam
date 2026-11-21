"""Construye data/processed/monthly.csv, el único archivo que lee la app.

Uso (desde la raíz del repo):
    python -m scripts.build_dataset

Brasil: datos reales (ONS, CMO/PLD, PTAX).
Chile:  datos reales del Coordinador Eléctrico Nacional (API + archivos descargados).
"""

import pandas as pd

from src.config import MONTHLY_FILE
from src.data import COLUMNAS
from src.lcoe import LCOE_ANUAL
from src.sources import brasil, chile


def main() -> None:
    br = brasil.mensual()
    br["lcoe"] = br.apply(lambda r: LCOE_ANUAL[r["tecnologia"]][r["fecha"].year], axis=1)
    br["fuente"] = "real"

    cl = chile.mensual()
    cl["lcoe"] = cl.apply(lambda r: LCOE_ANUAL[r["tecnologia"]][r["fecha"].year], axis=1)
    cl["fuente"] = "real"

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
