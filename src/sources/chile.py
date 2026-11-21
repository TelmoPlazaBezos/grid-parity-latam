"""Chile · Coordinador Eléctrico Nacional (API pública SIP).

- Costo marginal real horario (USD/MWh) por barra. La API solo cubre hasta el
  14/07/2024; desde el 15/07/2024 el Coordinador cambió el formato (15 min) y
  publica en otro sistema (pendiente de integrar).
- Generación horaria del sistema por tecnología (solar, eólica...).

Barras de referencia:
- Solar  -> Crucero 220 kV (Antofagasta, zona de mayor concentración solar)
- Eólica -> Charrúa 220 kV (Biobío, zona centro-sur con mucha eólica)
- Quillota 220 kV es la barra de referencia del sistema (se guarda también).

La clave `user_key` es la clave pública que usa la propia web del Coordinador.
"""

import json
from pathlib import Path
from typing import Dict
from urllib.request import urlopen

import pandas as pd

from src.config import ROOT

API = "https://sipubv1.api.coordinador.cl/api/v1/recursos"
USER_KEY = "f3cdad2758436a0a2c2c1fec92853de7"
RAW_DIR = ROOT / "data" / "raw" / "chile"
FIN_CMG_API = "2024-07-14"

BARRAS: Dict[str, str] = {
    "quillota": "BA02T0002SE032T0002",
    "crucero": "BA22T0027SE062G0216",
    "charrua": "BA03T0002SE009T0002",
}
BARRA_TECNOLOGIA = {"solar": "crucero", "eolica": "charrua"}


def _get_json(url: str, ruta: Path) -> dict:
    """Descarga con caché local en disco."""
    if not ruta.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        with urlopen(url, timeout=120) as r:
            ruta.write_bytes(r.read())
    return json.loads(ruta.read_text())


def _rango_mes(mes: pd.Timestamp) -> str:
    fin = mes + pd.offsets.MonthEnd(0)
    return f"fecha__gte={mes:%Y-%m-%d}&fecha__lte={fin:%Y-%m-%d}"


def costo_marginal(inicio: str = "2022-01", fin: str = FIN_CMG_API) -> pd.DataFrame:
    """Costo marginal real horario (USD/MWh) en las barras de referencia."""
    barras = ",".join(BARRAS.values())
    nombre = {v: k for k, v in BARRAS.items()}
    partes = []
    for mes in pd.date_range(inicio, fin, freq="MS"):
        url = f"{API}/costos_marginales_reales?user_key={USER_KEY}&barra_mnemotecnico__in={barras}&{_rango_mes(mes)}"
        datos = _get_json(url, RAW_DIR / f"cmg_{mes:%Y_%m}.json")["data"]
        partes.append(pd.DataFrame(datos))
    d = pd.concat(partes, ignore_index=True)
    d["hora"] = pd.to_datetime(d["fecha"]) + pd.to_timedelta(d["hora"] - 1, unit="h")
    d["barra"] = d["barra_mnemotecnico"].map(nombre)
    return d.pivot_table(index="hora", columns="barra", values="costo_en_dolares").reset_index()


def generacion(inicio: str = "2022-01", fin: str = "2025-12") -> pd.DataFrame:
    """Generación horaria del sistema (MWh) para solar y eólica."""
    partes = []
    for mes in pd.date_range(inicio, fin, freq="MS"):
        url = f"{API}/generacion_centrales_tecnologia_horario?user_key={USER_KEY}&{_rango_mes(mes)}"
        partes.append(pd.DataFrame(_get_json(url, RAW_DIR / f"gen_{mes:%Y_%m}.json")["aggs"]))
    d = pd.concat(partes, ignore_index=True)
    d = d[d["tipo_central"].isin(["solar", "eolica"])]
    d["hora"] = pd.to_datetime(d["fecha"]) + pd.to_timedelta(d["hora"] - 1, unit="h")
    return d.rename(columns={"tipo_central": "tecnologia", "generacion_sum": "generacion"})[
        ["hora", "tecnologia", "generacion"]]


def mensual() -> pd.DataFrame:
    """Precio base y capturado mensual por tecnología (periodo con CMg disponible)."""
    cmg = costo_marginal()
    gen = generacion()
    partes = []
    for tec, barra in BARRA_TECNOLOGIA.items():
        h = gen[gen["tecnologia"] == tec].merge(cmg[["hora", barra]], on="hora", how="inner")
        h = h.rename(columns={barra: "precio"})
        h["mes"] = h["hora"].dt.to_period("M").dt.to_timestamp()
        h["ingreso"] = h["precio"] * h["generacion"]
        g = h.groupby("mes").agg(generacion=("generacion", "sum"), ingreso=("ingreso", "sum"),
                                 precio_base=("precio", "mean"))
        partes.append(pd.DataFrame({
            "fecha": g.index, "pais": "CL", "tecnologia": tec,
            "precio_base": g["precio_base"].values,
            "precio_capturado": (g["ingreso"] / g["generacion"]).values,
            "generacion_mwh": g["generacion"].values,
        }))
    return pd.concat(partes, ignore_index=True)
