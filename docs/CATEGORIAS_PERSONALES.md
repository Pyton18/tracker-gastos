# Reglas de categorías “personales” (solo en tu máquina)

El repo incluye **`config/categorias.ejemplo.json`** con keywords **genéricas**, pensadas para el MVP web y para quien clone el proyecto.

Para tu uso privado (nombres de comercios, personas, etc.):

1. Copiá el ejemplo:  
   `config/categorias.ejemplo.json` → `config/categorias.json`
2. Editá `categorias.json` con tus palabras.
3. Ese archivo está en **`.gitignore`** y no se sube a Git.

En el **MVP web**, cada sesión arranca desde el ejemplo del repo; podés pegar tu JSON avanzado ahí si querés, o seguir usando el pipeline local con `scripts/run.py` y tu `categorias.json` personal.
