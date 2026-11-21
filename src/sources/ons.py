"""Brasil · ONS datos abiertos: generación y vertimiento (constrained-off).

Fuente: bucket público de ONS (CC BY 4.0), sin registro.
- Eólica:       dataset/restricao_coff_eolica_tm        (desde oct 2021)
- Fotovoltaica: dataset/restricao_coff_fotovoltaica_tm  (desde abr 2024)

Cada archivo mensual trae, por central y hora, la generación real y la
generación de referencia (la que habría producido sin restricción). La
energía vertida es la diferencia cuando el ONS aplicó una restricción.

Salida: tabla horaria por submercado y tecnología con generación y vertimiento
(MWh), que luego se cruza con el PLD horario para el precio capturado.
"""

from pathlib import Path
from typing import List
from urllib.request import urlretrieve

import pandas as pd

from src.config import ROOT

BASE_URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset"
RAW_DIR = ROOT / "data" / "raw" / "ons"

DATASETS = {
    "eolica": ("restricao_coff_eolica_tm", "RESTRICAO_COFF_EOLICA", "2021-10"),
    "solar": ("restricao_coff_fotovoltaica_tm", "RESTRICAO_COFF_FOTOVOLTAICA", "2024-04"),
}


def _meses(inicio: str, fin: str) -> List[pd.Timestamp]:
    return list(pd.date_range(inicio, fin, freq="MS"))


def descargar(tecnologia: str, inicio: str, fin: str) -> List[Path]:
    """Descarga (con caché local) los parquet mensuales de una tecnología."""
    carpeta, prefijo, primer_mes = DATASETS[tecnologia]
    inicio = max(pd.Timestamp(inicio), pd.Timestamp(primer_mes))
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    rutas = []
    for mes in _meses(inicio, fin):
        nombre = f"{prefijo}_{mes:%Y_%m}.parquet"
        ruta = RAW_DIR / nombre
        if not ruta.exists():
            urlretrieve(f"{BASE_URL}/{carpeta}/{nombre}", ruta)
        rutas.append(ruta)
    return rutas


def _procesar_archivo(ruta: Path) -> pd.DataFrame:
    """Agrega un archivo mensual a nivel hora x submercado."""
    cols = ["id_subsistema", "din_instante", "val_geracao", "val_geracaoreferencia",
            "val_geracaoreferenciafinal", "cod_razaorestricao"]
    d = pd.read_parquet(ruta, columns=cols)
    referencia = d["val_geracaoreferenciafinal"].fillna(d["val_geracaoreferencia"])
    restringido = d["cod_razaorestricao"].notna()
    d["vertido"] = (referencia - d["val_geracao"]).clip(lower=0).where(restringido, 0.0)
    d["generacion"] = d["val_geracao"].clip(lower=0)
    # Datos semihorarios en MW medios: energía de cada registro = MW x 0,5 h.
    d[["generacion", "vertido"]] *= 0.5
    d["hora"] = d["din_instante"].dt.floor("h")
    return d.groupby(["id_subsistema", "hora"], as_index=False)[["generacion", "vertido"]].sum()


def horario(tecnologia: str, inicio: str = "2022-01", fin: str = "2025-12") -> pd.DataFrame:
    """Generación y vertimiento horarios por submercado para una tecnología."""
    partes = [_procesar_archivo(r) for r in descargar(tecnologia, inicio, fin)]
    out = pd.concat(partes, ignore_index=True)
    out["tecnologia"] = tecnologia
    return out.rename(columns={"id_subsistema": "submercado"})
