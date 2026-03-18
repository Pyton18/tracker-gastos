"""
Script 3: Métricas sobre gastos categorizados.
- % de cumplimiento por categoría (100% = gastaste el tope, >100% = pasaste, <100% = no llegaste)
- Total = suma de las 5 categorías + Sin asignar
- Excluye pagos de tarjeta. Incluye ingresos (se suman como positivos).
"""

import json
from pathlib import Path

import pandas as pd

from .periodo import get_periodo_actual


def cargar_config() -> dict:
    """Carga la configuración del proyecto."""
    config_path = Path(__file__).parent.parent / "config" / "config.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def cargar_objetivos(objetivos_path: Path | None = None) -> dict:
    """
    Carga los topes de gasto.

    - Por defecto usa `config/objetivos.json` (y lo crea desde el ejemplo si no existe).
    - Para uso web, se puede pasar un `objetivos_path` específico por sesión.
    """
    if objetivos_path is None:
        base = Path(__file__).parent.parent / "config"
        objetivos_path = base / "objetivos.json"
        ejemplo_path = base / "objetivos.ejemplo.json"
        if not objetivos_path.exists() and ejemplo_path.exists():
            import shutil
            shutil.copy(ejemplo_path, objetivos_path)
            print("  (Se creó config/objetivos.json desde el ejemplo. Ajustá los montos.)")
    with open(objetivos_path, encoding="utf-8") as f:
        return json.load(f)


def calcular_metricas(
    periodo: str,
    ruta_categorizado: Path,
    ruta_salida: Path,
    objetivos_path: Path | None = None,
):
    """
    Calcula % de cumplimiento por categoría y total.
    Excluye: ingresos (monto > 0) y pagos de tarjeta.
    """
    archivo = ruta_categorizado / f"categorizado_{periodo}.xlsx"
    if not archivo.exists():
        print(f"No existe archivo categorizado para {periodo}")
        return

    df = pd.read_excel(archivo)
    objetivos = cargar_objetivos(objetivos_path=objetivos_path)

    df_gastos = df.copy()

    # Excluir pagos de tarjeta
    if objetivos.get("excluir", {}).get("pagos_tarjeta", True):
        mask_pago_tarjeta = df_gastos["descripcion"].fillna("").str.lower().str.contains("pago tarjeta")
        df_gastos = df_gastos[~mask_pago_tarjeta]

    # Suma por categoría (positivos y negativos)
    df_gastos["gasto"] = df_gastos["monto"]
    por_categoria = df_gastos.groupby("categoria", as_index=False)["gasto"].sum()

    categorias_config = objetivos.get("categorias", {})
    tope_total = objetivos.get("total", 0)

    # Tabla de resultados
    filas = []
    gasto_total = 0

    for cat, tope in categorias_config.items():
        gasto = por_categoria[por_categoria["categoria"] == cat]["gasto"].sum()
        gasto_total += gasto
        gasto_abs = abs(gasto) if gasto < 0 else 0
        pct = (gasto_abs / tope * 100) if tope else 0
        filas.append({
            "Categoria": cat,
            "Tope": tope,
            "Gastado": round(gasto, 2),  # negativo = gastos, positivo = ingresos
            "% Cumplimiento": round(pct, 1),
        })

    # Sin asignar (suma al total pero no tiene tope propio)
    gasto_sin_asignar = por_categoria[por_categoria["categoria"] == "Sin asignar"]["gasto"].sum()
    gasto_total += gasto_sin_asignar

    # Fila Total (gasto_total es negativo = gastos, positivo = ingresos netos)
    gasto_total_abs = abs(gasto_total) if gasto_total < 0 else 0
    pct_total = (gasto_total_abs / tope_total * 100) if tope_total else 0
    filas.append({
        "Categoria": "Total",
        "Tope": tope_total,
        "Gastado": round(gasto_total, 2),
        "% Cumplimiento": round(pct_total, 1),
    })

    # Fila Sin asignar (informativa, sin %)
    filas.insert(-1, {
        "Categoria": "Sin asignar",
        "Tope": "-",
        "Gastado": round(gasto_sin_asignar, 2),
        "% Cumplimiento": "-",
    })

    df_resultado = pd.DataFrame(filas)

    # Guardar
    ruta_salida.mkdir(parents=True, exist_ok=True)
    out_file = ruta_salida / f"metricas_{periodo}.xlsx"
    df_resultado.to_excel(out_file, index=False)

    # Mostrar en consola
    print(f"\nPeriodo {periodo}:")
    print(df_resultado.to_string(index=False))
    print(f"\n  Guardado: {out_file.name}")


def metricas():
    """Punto de entrada principal."""
    config = cargar_config()
    base = Path(__file__).parent.parent
    ruta_categorizado = base / config["rutas"]["categorizado"]
    ruta_salida = base / config["rutas"]["metricas"]

    res = get_periodo_actual()
    if not res:
        print("No se pudo detectar ningún período.")
        return
    periodo, _ = res
    calcular_metricas(periodo, ruta_categorizado, ruta_salida)


if __name__ == "__main__":
    metricas()
