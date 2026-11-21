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
from datetime import datetime
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
    """Precio base, precio capturado y vertimiento mensual por tecnología."""
    cmg = pd.concat([costo_marginal(), costo_marginal_descargado()], ignore_index=True)
    gen = generacion()
    vert = vertimiento_mensual()
    partes = []
    for tec, barra in BARRA_TECNOLOGIA.items():
        # left join: los meses sin costo marginal conservan generación y vertimiento.
        h = gen[gen["tecnologia"] == tec].merge(cmg[["hora", barra]], on="hora", how="left")
        h = h.rename(columns={barra: "precio"})
        h["mes"] = h["hora"].dt.to_period("M").dt.to_timestamp()
        h["ingreso"] = h["precio"] * h["generacion"]
        h["gen_con_precio"] = h["generacion"].where(h["precio"].notna())
        g = h.groupby("mes").agg(generacion=("generacion", "sum"), ingreso=("ingreso", "sum"),
                                 gen_con_precio=("gen_con_precio", "sum"),
                                 precio_base=("precio", "mean"))
        v = vert[vert["tecnologia"] == tec].set_index("fecha")["vertido_mwh"].reindex(g.index)
        partes.append(pd.DataFrame({
            "fecha": g.index, "pais": "CL", "tecnologia": tec,
            "precio_base": g["precio_base"].values,
            "precio_capturado": (g["ingreso"] / g["gen_con_precio"].replace(0, float("nan"))).values,
            "vertimiento": (v / (v + g["generacion"])).values,
            "generacion_mwh": g["generacion"].values,
        }))
    return pd.concat(partes, ignore_index=True)


# --- Desde el 15/07/2024: archivos descargados a mano del visor del Coordinador ---
# Visor: coordinador.cl > Mercados > Descarga Datos Costos Marginales > Preliminar/Real
# Filtros: Año, Mes, Barras (Quillota/Crucero/Charrúa 220), Descargar (.xlsx, 15 min).
# Los archivos se guardan en data/external/chile_cmg/ y sí se suben al repo.
EXTERNAL_DIR = ROOT / "data" / "external" / "chile_cmg"
COLUMNAS_XLSX = {"QUILLOTA": "quillota", "CRUCERO": "crucero", "CHARRUA": "charrua"}


def costo_marginal_descargado() -> pd.DataFrame:
    """Lee los .xlsx del visor y devuelve el costo marginal horario por barra (USD/MWh)."""
    partes = []
    for ruta in sorted(EXTERNAL_DIR.glob("*.xlsx")):
        d = pd.read_excel(ruta)
        cols = {c: n for c in d.columns for k, n in COLUMNAS_XLSX.items() if c.upper().startswith(k)}
        d = d.rename(columns=cols)
        # 'Hora' va de 0 a 23 y 'Minutos' de 0 a 45: se promedian los 4 cuartos de hora.
        d["hora"] = pd.to_datetime(d["Fecha"]) + pd.to_timedelta(d["Hora"], unit="h")
        partes.append(d.groupby("hora", as_index=False)[list(cols.values())].mean())
    out = pd.concat(partes, ignore_index=True).drop_duplicates("hora")
    return out[out["hora"] > pd.Timestamp(FIN_CMG_API) + pd.Timedelta(days=1)]


# --- Vertimiento (reducciones ERV) publicado por el Coordinador ---
# Coordinador > Operación > Documentos > Reducciones de Generación Renovable.
# Se usa el archivo de diciembre de cada año: su hoja 'Resumen-Mensual' trae
# los GWh reducidos de cada mes del año, por tecnología.
REDUCCIONES_URLS = {
    2022: "2023/01/Reducciones-de-Energia-Eolica-y-Solar-en-el-SEN_Diciembre-2022.xlsx",
    2023: "2024/01/Reducciones-de-Energia-Eolica-y-Solar-en-el-SEN_Diciembre-2023_v2.xlsx",
    2024: "2025/01/Reducciones-de-Energia-Eolica-y-Solar-en-el-SEN_Diciembre-24-PE-PFV_Publicar.xlsx",
    2025: "2026/01/Reducciones-de-Energia-Eolica-Solar-Hidro-en-el-SEN_Diciembre-25-PE-PFV_Publicar.xlsx",
}
ETIQUETAS = {"Eólica": "eolica", "Solar": "solar"}


def vertimiento_mensual() -> pd.DataFrame:
    """Energía reducida (MWh) por mes y tecnología, 2022-2025."""
    from urllib.request import urlretrieve

    filas = []
    for anio, ruta_web in REDUCCIONES_URLS.items():
        ruta = RAW_DIR / f"reducciones_{anio}.xlsx"
        if not ruta.exists():
            RAW_DIR.mkdir(parents=True, exist_ok=True)
            urlretrieve(f"https://www.coordinador.cl/wp-content/uploads/{ruta_web}", ruta)
        d = pd.read_excel(ruta, sheet_name="Resumen-Mensual", header=None)
        # Fila de cabecera: la que tiene fechas de inicio de mes del año.
        fila_fechas = next(i for i in range(len(d))
                           if isinstance(d.iat[i, 2], datetime) and d.iat[i, 2].year == anio)
        cols = {j: pd.Timestamp(d.iat[fila_fechas, j]) for j in range(d.shape[1])
                if isinstance(d.iat[fila_fechas, j], datetime)}
        for i in range(fila_fechas + 1, fila_fechas + 6):
            tec = ETIQUETAS.get(str(d.iat[i, 1]).strip())
            if tec:
                for j, mes in cols.items():
                    filas.append({"fecha": mes, "tecnologia": tec,
                                  "vertido_mwh": pd.to_numeric(d.iat[i, j], errors="coerce") * 1000})
    return pd.DataFrame(filas)
