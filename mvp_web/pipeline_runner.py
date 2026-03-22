from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

import pandas as pd

from src.estandarizar import procesar_periodo
from src.categorizar import categorizar_periodo
from src.metricas import calcular_metricas

from .periodo_web import inferir_periodo_desde_inputs


def _validate_categorias_json(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["categorias.json debe ser un objeto JSON"]
    if "categorias" in data and not isinstance(data.get("categorias"), list):
        errors.append('"categorias" debe ser una lista')
    for i, cat in enumerate(data.get("categorias", [])):
        if not isinstance(cat, dict):
            errors.append(f"categorias[{i}] debe ser un objeto")
            continue
        nombre = cat.get("nombre")
        if not isinstance(nombre, str) or not nombre.strip():
            errors.append(f"categorias[{i}].nombre es requerido")
        for patron in cat.get("regex", []) or []:
            if not isinstance(patron, str):
                errors.append(f"categorias[{i}].regex contiene un valor no-string")
                continue
            try:
                re.compile(patron)
            except re.error as e:
                errors.append(f"categorias[{i}].regex inválido: {patron!r} ({e})")
    return errors


def _validate_objetivos_json(data: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["objetivos.json must be a JSON object"]
    cats = data.get("categorias")
    if cats is None:
        errors.append('"categorias" is required (object: category name -> budget amount)')
    elif not isinstance(cats, dict):
        errors.append('"categorias" must be an object')
    else:
        for k, v in cats.items():
            if not isinstance(k, str) or not k.strip():
                errors.append(f"invalid category key: {k!r}")
                continue
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                errors.append(f"budget for {k!r} must be a number")
    total = data.get("total")
    if total is not None and (isinstance(total, bool) or not isinstance(total, (int, float))):
        errors.append('"total" must be a number (overall monthly budget cap)')
    excl = data.get("excluir")
    if excl is not None:
        if not isinstance(excl, dict):
            errors.append('"excluir" must be an object')
        elif "pagos_tarjeta" in excl and not isinstance(excl.get("pagos_tarjeta"), bool):
            errors.append('"excluir.pagos_tarjeta" must be a boolean')
    return errors


def validate_and_write_objetivos_json(path: Path, raw_json: str) -> tuple[bool, list[str]]:
    try:
        data = json.loads(raw_json)
    except Exception as e:
        return False, [f"Invalid JSON: {e}"]
    errors = _validate_objetivos_json(data)
    if errors:
        return False, errors
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, []


def validate_and_write_categorias_json(path: Path, raw_json: str) -> tuple[bool, list[str]]:
    try:
        data = json.loads(raw_json)
    except Exception as e:
        return False, [f"JSON inválido: {e}"]
    errors = _validate_categorias_json(data)
    if errors:
        return False, errors
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return True, []


def compute_summary(periodo: str, categorizado_path: Path, metricas_path: Path) -> dict:
    summary: dict = {"periodo": periodo}
    try:
        df_cat = pd.read_excel(categorizado_path)
        sin_asignar = (
            df_cat[df_cat.get("categoria") == "Sin asignar"]["descripcion"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        summary["sin_asignar"] = sorted(sin_asignar)[:250]
        summary["counts"] = {
            "rows_categorizado": int(len(df_cat)),
            "unique_sin_asignar": int(len(set(sin_asignar))),
        }
    except Exception:
        pass
    try:
        df_met = pd.read_excel(metricas_path)
        summary["metricas"] = df_met.to_dict(orient="records")
    except Exception:
        summary["metricas"] = []
    return summary


def run_pipeline_for_session(
    periodo: str | None,
    inputs_dir: Path,
    outputs_dir: Path,
    categorias_path: Path,
    objetivos_path: Path,
    *,
    formato: str = "xlsx",
) -> dict:
    """
    Ejecuta los 3 pasos usando carpetas por sesión.
    Devuelve un summary serializable para la UI.

    Si ``periodo`` es None, vacío o ``auto``, se infiere YYYY-MM desde las fechas
    de los movimientos importados (fecha máxima). Eso **no filtra** filas: solo
    define etiqueta/nombre de salida. Un valor explícito (solo uso programático)
    tampoco filtra; la web ya no envía período manual.
    """
    outputs_dir.mkdir(parents=True, exist_ok=True)

    raw = (periodo or "").strip()
    pl = raw.lower()
    if not pl or pl == "auto":
        periodo = inferir_periodo_desde_inputs(inputs_dir)
        periodo_inferido = True
    else:
        periodo = raw
        if len(periodo) != 7 or periodo[4] != "-":
            raise ValueError("Período inválido. Usá YYYY-MM o dejalo en automático.")
        periodo_inferido = False

    # 1) estandarizar -> genera estandarizado_{periodo}.xlsx en outputs_dir/estandarizado
    estandarizado_dir = outputs_dir / "estandarizado"
    categorizado_dir = outputs_dir / "categorizado"
    metricas_dir = outputs_dir / "metricas"
    estandarizado_dir.mkdir(parents=True, exist_ok=True)
    categorizado_dir.mkdir(parents=True, exist_ok=True)
    metricas_dir.mkdir(parents=True, exist_ok=True)

    procesar_periodo(periodo, inputs_dir, estandarizado_dir, formato=formato)

    # 2) categorizar
    categorizar_periodo(
        periodo,
        estandarizado_dir,
        categorizado_dir,
        mostrar_sin_asignar=False,
        categorias_path=categorias_path,
    )

    # 3) métricas
    calcular_metricas(periodo, categorizado_dir, metricas_dir, objetivos_path=objetivos_path)

    estandarizado_file = estandarizado_dir / f"estandarizado_{periodo}.xlsx"
    categorizado_file = categorizado_dir / f"categorizado_{periodo}.xlsx"
    metricas_file = metricas_dir / f"metricas_{periodo}.xlsx"

    summary = compute_summary(periodo, categorizado_file, metricas_file)
    summary["periodo_inferido"] = periodo_inferido
    summary["outputs"] = {
        "estandarizado": str(estandarizado_file),
        "categorizado": str(categorizado_file),
        "metricas": str(metricas_file),
    }
    return summary


def new_run_id() -> str:
    return uuid.uuid4().hex

