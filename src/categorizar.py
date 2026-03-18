"""
Script 2: Categorizar gastos mediante keywords/regex.
- Lee archivo(s) estandarizados
- Aplica reglas de config/categorias.json (keywords o regex)
- "Sin asignar" para lo que no pudo inferir
"""

import json
import re
from pathlib import Path

import pandas as pd

from .periodo import get_periodo_actual


def cargar_config() -> dict:
    """Carga la configuración del proyecto."""
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def cargar_categorias(categorias_path: Path | None = None) -> dict:
    """
    Carga las reglas de categorización.

    - Por defecto usa `config/categorias.json` (y lo crea desde el ejemplo si no existe).
    - Para uso web, se puede pasar un `categorias_path` específico por sesión.
    """
    if categorias_path is None:
        base = Path(__file__).parent.parent / "config"
        categorias_path = base / "categorias.json"
        ejemplo_path = base / "categorias.ejemplo.json"
        if not categorias_path.exists() and ejemplo_path.exists():
            import shutil
            shutil.copy(ejemplo_path, categorias_path)
            print("  (Se creó config/categorias.json desde el ejemplo. Personalizalo.)")
    with open(categorias_path, encoding="utf-8") as f:
        return json.load(f)


def categorizar_descripcion(descripcion: str, categorias: dict) -> str:
    """
    Categoriza usando keywords (substring) o regex.
    Keywords: si la palabra está en la descripción (case insensitive) → match.
    """
    fallback = categorias.get("fallback", "Sin asignar")
    texto = str(descripcion or "").lower()

    for cat in categorias.get("categorias", []):
        nombre = cat.get("nombre", "")
        for kw in cat.get("keywords", []):
            if kw.lower() in texto:
                return nombre
        for patron in cat.get("regex", []):
            try:
                if re.search(patron, texto, re.IGNORECASE):
                    return nombre
            except re.error:
                continue

    return fallback


def categorizar_periodo(
    periodo: str,
    ruta_estandarizado: Path,
    ruta_salida: Path,
    mostrar_sin_asignar: bool = False,
    categorias_path: Path | None = None,
):
    """
    Procesa un archivo estandarizado y genera el categorizado.
    """
    archivo = ruta_estandarizado / f"estandarizado_{periodo}.xlsx"
    if not archivo.exists():
        print(f"No existe archivo estandarizado para {periodo}")
        return

    df = pd.read_excel(archivo)
    categorias = cargar_categorias(categorias_path=categorias_path)

    df["categoria"] = df["descripcion"].apply(lambda d: categorizar_descripcion(d, categorias))

    salida = ruta_salida / f"categorizado_{periodo}.xlsx"
    df.to_excel(salida, index=False)
    print(f"  Guardado: {salida.name} ({len(df)} filas)")

    if mostrar_sin_asignar:
        sin_asignar = df[df["categoria"] == "Sin asignar"]["descripcion"].dropna().unique()
        if len(sin_asignar) > 0:
            print(f"\n  Sin asignar ({len(sin_asignar)} descripciones distintas):")
            for desc in sorted(sin_asignar, key=str):
                print(f"    - {str(desc)[:80]}")


def categorizar():
    """Punto de entrada principal."""
    config = cargar_config()
    base = Path(__file__).parent.parent
    ruta_estandarizado = base / config["rutas"]["estandarizado"]
    ruta_salida = base / config["rutas"]["categorizado"]
    
    ruta_salida.mkdir(parents=True, exist_ok=True)
    mostrar_sin_asignar = config.get("reporte_sin_asignar", False)

    res = get_periodo_actual()
    if not res:
        print("No se pudo detectar ningún período.")
        return
    periodo, _ = res
    categorizar_periodo(periodo, ruta_estandarizado, ruta_salida, mostrar_sin_asignar=mostrar_sin_asignar)


if __name__ == "__main__":
    categorizar()
