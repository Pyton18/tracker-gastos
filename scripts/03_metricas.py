"""
Punto de entrada: Calcular métricas.
Uso: python scripts/03_metricas.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.metricas import metricas

if __name__ == "__main__":
    metricas()
