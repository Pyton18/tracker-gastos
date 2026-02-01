"""
Punto de entrada: Categorizar gastos.
Uso: python scripts/02_categorizar.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.categorizar import categorizar

if __name__ == "__main__":
    categorizar()
