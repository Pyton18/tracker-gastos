"""
Inferencia de período (YYYY-MM) para el MVP web cuando no hay carpetas Gastos/YYYY-MM.
Se basa en la fecha máxima encontrada en los movimientos importados.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.estandarizar import listar_archivos_a_procesar
from src.importadores import _detectar_tipo_archivo, importar_archivo


def inferir_periodo_desde_inputs(inputs_dir: Path) -> str:
    """
    Importa todos los archivos reconocidos (sin escribir salida), concatena y
    devuelve YYYY-MM según la fecha máxima de los movimientos.
    """
    archivos = listar_archivos_a_procesar(inputs_dir)
    placeholder = "2000-01"
    dfs = []
    for arch in archivos:
        tipo = _detectar_tipo_archivo(arch)
        if not tipo:
            continue
        df = importar_archivo(arch, placeholder, debug=False)
        if not df.empty:
            dfs.append(df)

    if not dfs:
        raise ValueError(
            "No se pudo importar ningún archivo reconocido. "
            "Asegurate de subir extractos de Mercado Pago (account_statement), "
            "movimientos banco / PDF Santander, o consumos tarjeta."
        )

    combined = pd.concat(dfs, ignore_index=True)
    combined["fecha"] = pd.to_datetime(combined["fecha"], errors="coerce")
    valid = combined.dropna(subset=["fecha"])
    if valid.empty:
        raise ValueError("No hay fechas válidas en los archivos subidos.")

    max_dt = valid["fecha"].max()
    return max_dt.strftime("%Y-%m")
