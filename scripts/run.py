"""
Script madre: ejecuta los 3 scripts en orden (importar → categorizar → métricas).
Uso: python scripts/run.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.estandarizar import estandarizar
from src.categorizar import categorizar
from src.metricas import metricas


if __name__ == "__main__":
    print("=== 1. Importar y estandarizar ===")
    estandarizar()
    print("\n=== 2. Categorizar ===")
    categorizar()
    print("\n=== 3. Métricas ===")
    metricas()
    print("\n--- Listo ---")
