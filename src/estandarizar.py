"""
Script 1: Importar archivos, estandarizar datos, guardar en XLS.
- Lee archivos de la carpeta de entrada (Gastos o subcarpetas YYYY-MM)
- Detecta formato (CSV, XLSX) y mapea columnas al esquema estándar
- Unifica fechas, montos y descripciones
- Guarda un archivo por período en data/estandarizado/
"""

import json
from pathlib import Path

from .importadores import importar_archivo, _detectar_tipo_archivo
from .esquema import COLUMNAS_ESTANDAR
from .periodo import get_periodo_actual


def cargar_config() -> dict:
    """Carga la configuración del proyecto."""
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def listar_archivos_a_procesar(ruta: Path) -> list[Path]:
    """Lista archivos CSV y XLSX en la ruta. Excluye temp de Excel (~$)."""
    extensiones = {".csv", ".xlsx", ".xls", ".pdf"}
    archivos = []
    for ext in extensiones:
        archivos.extend(ruta.glob(f"*{ext}"))
    archivos = [a for a in archivos if not a.name.startswith("~$")]
    return sorted(archivos)


def procesar_periodo(periodo: str, ruta: Path, salida: Path, formato: str) -> int:
    """Importa y guarda los datos de un período. Devuelve cantidad de registros."""
    archivos = listar_archivos_a_procesar(ruta)
    import pandas as pd

    config = cargar_config()
    debug = config.get("debug_import", False)

    dfs = []
    for arch in archivos:
        tipo = _detectar_tipo_archivo(arch)
        if not tipo:
            print(f"  Saltando (tipo desconocido): {arch.name}")
            continue
        df = importar_archivo(arch, periodo, debug=debug)
        if not df.empty:
            dfs.append(df)
            print(f"  {tipo}: {arch.name} -> {len(df)} registros")

    if not dfs:
        return 0

    df_final = pd.concat(dfs, ignore_index=True)
    df_final = df_final[COLUMNAS_ESTANDAR]
    # Evitar doble importación cuando conviven fuentes (p.ej. XLS + PDF del mismo período)
    df_final = df_final.drop_duplicates(subset=["fecha", "descripcion", "monto"], keep="first")
    df_final = df_final.sort_values(["fecha", "origen"])

    salida.mkdir(parents=True, exist_ok=True)
    out_file = salida / f"estandarizado_{periodo}.xlsx"
    df_final.to_excel(out_file, index=False)
    print(f"  Guardado: {out_file.name} ({len(df_final)} filas)")
    return len(df_final)


def estandarizar():
    """Punto de entrada principal."""
    config = cargar_config()
    base = Path(__file__).parent.parent
    entrada = base / config["rutas"]["entrada"]
    salida = base / config["rutas"]["estandarizado"]
    formato = config.get("formato_salida", "xlsx")

    if not entrada.exists():
        raise FileNotFoundError(f"Carpeta de entrada no encontrada: {entrada}")

    res = get_periodo_actual()
    if not res:
        print("No se pudo detectar ningún período.")
        return
    periodo, ruta = res
    archivos = listar_archivos_a_procesar(ruta)
    if archivos:
        print(f"Periodo {periodo}: {len(archivos)} archivo(s)")
        procesar_periodo(periodo, ruta, salida, formato)
    else:
        print(f"Periodo {periodo}: sin archivos")


if __name__ == "__main__":
    estandarizar()
