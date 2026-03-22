"""
Keep session objetivos.json (budget caps) in sync with categorias.json when the
user edits budgets from the friendly UI: add/remove category names and stub rules.
"""
from __future__ import annotations

import json
from pathlib import Path

# Must not be used as a user category name (pipeline / metrics semantics)
RESERVED_NAMES = frozenset(
    {
        "",
        "Sin asignar",
        "Total",
        "sin asignar",
        "total",
    }
)


def normalize_category_name(name: str) -> str:
    return (name or "").strip()


def apply_budget_save(
    objetivos_path: Path,
    categorias_path: Path,
    *,
    total: float,
    categories: list[tuple[str, float]],
) -> list[str]:
    """
    Writes objetivos and updates categorias rules:
    - Removes rules for category names that were removed from the budget list.
    - Appends {nombre, keywords: []} for new budget categories missing from rules.

    Returns list of validation error strings (empty if ok).
    """
    errors: list[str] = []
    seen: set[str] = set()
    cleaned: list[tuple[str, float]] = []
    for raw_name, budget in categories:
        name = normalize_category_name(raw_name)
        if not name:
            errors.append("Category name cannot be empty.")
            continue
        if name in RESERVED_NAMES:
            errors.append(f"Reserved name: {name!r}")
            continue
        if name in seen:
            errors.append(f"Duplicate category: {name!r}")
            continue
        seen.add(name)
        try:
            b = float(budget)
        except (TypeError, ValueError):
            errors.append(f"Invalid budget for {name!r}")
            continue
        if b < 0:
            errors.append(f"Budget cannot be negative: {name!r}")
            continue
        cleaned.append((name, b))

    if errors:
        return errors

    try:
        total_f = float(total)
    except (TypeError, ValueError):
        return ["Invalid total budget."]
    if total_f < 0:
        return ["Total budget cannot be negative."]

    obj = json.loads(objetivos_path.read_text(encoding="utf-8"))
    old_keys = set((obj.get("categorias") or {}).keys())
    new_keys = {n for n, _ in cleaned}
    removed = old_keys - new_keys
    added = new_keys - old_keys

    # Preserve objetivos structure (descripcion, excluir, etc.)
    obj["total"] = total_f
    obj["categorias"] = {name: b for name, b in cleaned}
    objetivos_path.parent.mkdir(parents=True, exist_ok=True)
    objetivos_path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    cat = json.loads(categorias_path.read_text(encoding="utf-8"))
    arr = list(cat.get("categorias") or [])

    # Drop rules for removed budget categories
    if removed:
        arr = [c for c in arr if c.get("nombre") not in removed]

    existing = {c.get("nombre") for c in arr if isinstance(c, dict)}

    for name in added:
        if name not in existing:
            arr.append({"nombre": name, "keywords": []})
            existing.add(name)

    cat["categorias"] = arr
    categorias_path.parent.mkdir(parents=True, exist_ok=True)
    categorias_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2), encoding="utf-8")

    return []


def budget_state_for_template(objetivos_path: Path) -> dict:
    """Serializable state for the home page UI."""
    obj = json.loads(objetivos_path.read_text(encoding="utf-8"))
    cats = obj.get("categorias") or {}
    categories = [{"name": k, "budget": v} for k, v in cats.items()]
    return {
        "total": obj.get("total", 0),
        "categories": categories,
        "excluir_pagos_tarjeta": (obj.get("excluir") or {}).get("pagos_tarjeta", True),
    }
