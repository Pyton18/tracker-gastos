"""
Debug: muestra qué keyword matcheó para una descripción.
Uso: python scripts/debug_categoria.py "Transferencias inmediatas A sanguinetti..."
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.categorizar import cargar_categorias


def debug_descripcion(descripcion: str):
    categorias = cargar_categorias()
    texto = (descripcion or "").lower()

    print(f'Descripcion: "{descripcion[:80]}..."' if len(descripcion) > 80 else f'Descripcion: "{descripcion}"')
    print(f'Texto (lower): "{texto[:80]}..."' if len(texto) > 80 else f'Texto (lower): "{texto}"')
    print()

    for cat in categorias.get("categorias", []):
        nombre = cat.get("nombre", "")
        for kw in cat.get("keywords", []):
            if kw.lower() in texto:
                print(f'  MATCH: categoria="{nombre}", keyword="{kw}"')
                return
        for patron in cat.get("regex", []):
            try:
                import re
                if re.search(patron, texto, re.IGNORECASE):
                    print(f'  MATCH: categoria="{nombre}", regex="{patron}"')
                    return
            except re.error:
                pass

    print(f'  SIN MATCH -> fallback="{categorias.get("fallback", "Sin asignar")}"')


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scripts/debug_categoria.py \"descripcion del movimiento\"")
        sys.exit(1)
    debug_descripcion(sys.argv[1])
