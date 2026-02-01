"""
Detecta y gestiona el período a procesar.
Los scripts 01, 02, 03 usan get_periodo_actual() para saber sobre cuál período trabajar.
"""
import json
import re
from pathlib import Path


def cargar_config() -> dict:
    """Carga la configuración del proyecto."""
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def _detectar_periodo_mas_reciente(carpeta_entrada: Path) -> tuple[str, Path] | None:
    """
    Detecta el período más reciente en Gastos.
    - Si hay subcarpetas YYYY-MM: retorna (periodo, ruta) del más reciente
    - Si no: retorna ("prueba", carpeta_entrada)
    """
    if not carpeta_entrada.exists():
        return None

    subcarpetas = [d for d in carpeta_entrada.iterdir() if d.is_dir()]
    patron = re.compile(r"^\d{4}-\d{2}$")
    carpetas_mes = [d for d in subcarpetas if patron.match(d.name)]

    if carpetas_mes:
        mas_reciente = max(carpetas_mes, key=lambda d: d.name)
        return (mas_reciente.name, mas_reciente)
    return ("prueba", carpeta_entrada)


def get_periodo_actual() -> tuple[str, Path] | None:
    """
    Devuelve (periodo, ruta) a procesar.
    - Si config tiene "periodo_actual" con valor, lo usa.
    - Si no, auto-detecta el período más reciente en Gastos.
    """
    config = cargar_config()
    base = Path(__file__).parent.parent
    entrada = base / config["rutas"]["entrada"]
    periodo_config = config.get("periodo_actual")

    if periodo_config:
        ruta = entrada / str(periodo_config)
        if ruta.is_dir():
            return (str(periodo_config), ruta)
        return (str(periodo_config), entrada)

    return _detectar_periodo_mas_reciente(entrada)
