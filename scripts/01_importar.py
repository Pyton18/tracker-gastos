"""
Punto de entrada: Importar y estandarizar gastos.
Uso: python scripts/01_importar.py
"""
import sys
from pathlib import Path

# Agregar raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.estandarizar import estandarizar

if __name__ == "__main__":
    estandarizar()
