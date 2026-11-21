"""Brasil · precio horario en USD/MWh.

El PLD oficial lo publica la CCEE, pero su portal bloquea descargas
automatizadas. Se reconstruye a partir del CMO semihorario del ONS (el PLD
horario sale del mismo modelo DESSEM), acotado por el PLD mínimo y máximo
horario regulados por ANEEL para cada año.

Límites del PLD (ANEEL): 2023, 2024 y 2025 verificados en prensa sectorial
(Canal Solar). 2022 pendiente de verificar.

Tipo de cambio: PTAX (venta) del Banco Central do Brasil, API abierta Olinda.
"""

import json
from pathlib import Path
from urllib.request import urlopen, urlretrieve

import pandas as pd

from src.config import ROOT

ONS_CMO = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/cmo_tm/CMO_SEMIHORARIO_{anio}.parquet"
PTAX_URL = ("https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
            "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
            "?@dataInicial='{ini}'&@dataFinalCotacao='{fin}'&$format=json")
RAW_DIR = ROOT / "data" / "raw" / "brasil"

# PLD mínimo y máximo horario (R$/MWh) por año, fijados por ANEEL.
PLD_LIMITES = {
    2022: (55.70, 1326.50),  # pendiente de verificar
    2023: (69.04, 1391.56),
    2024: (61.07, 1470.47),
    2025: (58.60, 1542.23),
}


def _descargar_cmo(anio: int) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    ruta = RAW_DIR / f"CMO_SEMIHORARIO_{anio}.parquet"
    if not ruta.exists():
        urlretrieve(ONS_CMO.format(anio=anio), ruta)
    return ruta


def pld_horario_brl(anio: int) -> pd.DataFrame:
    """PLD horario aproximado (R$/MWh) por submercado para un año."""
    d = pd.read_parquet(_descargar_cmo(anio))
    d["val_cmo"] = pd.to_numeric(d["val_cmo"].astype(str).str.replace(",", "."), errors="coerce")
    d["hora"] = pd.to_datetime(d["din_instante"]).dt.floor("h")
    h = d.groupby(["id_subsistema", "hora"], as_index=False)["val_cmo"].mean()
    piso, techo = PLD_LIMITES[anio]
    h["pld_brl"] = h["val_cmo"].clip(lower=piso, upper=techo)
    return h.rename(columns={"id_subsistema": "submercado"})[["submercado", "hora", "pld_brl"]]


def ptax_diario(inicio: str, fin: str) -> pd.Series:
    """Cotización PTAX de venta (BRL por USD) diaria entre dos fechas (YYYY-MM-DD)."""
    ruta = RAW_DIR / f"ptax_{inicio}_{fin}.json"
    if not ruta.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        i, f = pd.Timestamp(inicio), pd.Timestamp(fin)
        url = PTAX_URL.format(ini=f"{i:%m-%d-%Y}", fin=f"{f:%m-%d-%Y}")
        with urlopen(url, timeout=60) as r:
            ruta.write_bytes(r.read())
    valores = json.loads(ruta.read_text())["value"]
    s = pd.DataFrame(valores)
    s["fecha"] = pd.to_datetime(s["dataHoraCotacao"]).dt.normalize()
    return s.groupby("fecha")["cotacaoVenda"].last()


def pld_horario_usd(anios: range = range(2022, 2026)) -> pd.DataFrame:
    """PLD horario en USD/MWh por submercado (PTAX del día; fines de semana, último hábil)."""
    pld = pd.concat([pld_horario_brl(a) for a in anios], ignore_index=True)
    ptax = ptax_diario(f"{anios.start}-01-01", f"{anios.stop - 1}-12-31")
    dias = pd.date_range(ptax.index.min(), f"{anios.stop - 1}-12-31", freq="D")
    ptax = ptax.reindex(dias).ffill()
    pld["fecha"] = pld["hora"].dt.normalize()
    pld["ptax"] = pld["fecha"].map(ptax).bfill()
    pld["precio_usd"] = pld["pld_brl"] / pld["ptax"]
    return pld[["submercado", "hora", "precio_usd"]]
