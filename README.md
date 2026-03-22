# Tracker de Gastos

Pipeline para importar extractos bancarios, categorizar movimientos y calcular métricas de cumplimiento de presupuesto.

**Requisitos:** Python 3.10+

---

## Qué hace

1. **Importar** — Lee archivos Excel/CSV de Mercado Pago, cuenta bancaria (débito) y tarjeta de crédito. Estandariza todo a un mismo formato.
2. **Categorizar** — Asigna cada movimiento a una categoría usando keywords (ej: "supermercado" → Abastecimiento).
3. **Métricas** — Calcula el % de cumplimiento por categoría vs. los topes que definas.

---

## Instalación

```bash
git clone https://github.com/TU_USUARIO/tracker-gastos.git
cd tracker-gastos
pip install -r requirements.txt
```

Crear la carpeta donde irán tus extractos:

```bash
mkdir Gastos
```

(En Windows: `md Gastos`)

---

## Primera vez

Al correr el pipeline por primera vez, se crearán automáticamente:

- `config/categorias.json` — desde el ejemplo. **Editalo:** reemplazá `NOMBRE_PERSONA_1`, etc. por los nombres reales que querés mapear a categorías fijas (ej: quien limpia → Vivienda y Fijos).
- `config/objetivos.json` — desde el ejemplo. **Editalo:** ajustá los montos de cada categoría y el total.

---

## Uso mensual

1. Crear una carpeta por mes dentro de `Gastos`, por ejemplo: `Gastos/2025-02/`
2. Copiar ahí tus 3 archivos: extracto Mercado Pago, movimientos de la cuenta, consumos de la tarjeta de crédito
3. Ejecutar:

```bash
python scripts/run.py
```

Eso ejecuta los 3 pasos en orden. Los resultados quedan en `data/`:
- `data/estandarizado/` — movimientos unificados
- `data/categorizado/` — con columna de categoría
- `data/metricas/` — % de cumplimiento por categoría

El script procesa **siempre el período más reciente** (la carpeta YYYY-MM con el número más alto). Para forzar otro mes, editá `config/config.json` y poné `"periodo_actual": "2025-01"`.

---

## Descarga de extractos (guía rápida)

Este repo no automatiza la descarga: asume que vos bajás los archivos y los dejás en `Gastos/YYYY-MM/`.

- **Mercado Pago (extracto `account_statement`)**
  - **Objetivo**: generar un Excel con nombre tipo `account_statement-....xlsx` (o que contenga columnas `RELEASE_DATE`, `TRANSACTION_TYPE`, `TRANSACTION_NET_AMOUNT`).
  - **Pasos (web)**
    - Entrar a **Cuenta → Tu dinero**
    - En **Movimientos**, hacer click en **Consultar todos**
    - Click en **Generar Resumen de cuenta**
    - En “Tus resúmenes de cuenta”, elegir **Período personalizado** (acá elegís **desde** y **hasta**, hasta 31 días)
      - Nota: también podés elegir un mes “prearmado” (ej: “Enero 2026”). Es redundante con “Período personalizado”, pero a veces es la forma más directa de llegar al selector correcto.
    - Elegir **Formato: .xlsx**
    - Generar y descargar
  - **Dónde lo pongo**: `Gastos/YYYY-MM/` (ej: `Gastos/2026-01/account_statement-....xlsx`)

- **Cuenta / Débito (Santander)**
  - **Excel “movimientos”**: si lo podés exportar, dejalo como `movimientos.xlsx`.
  - **PDF “Mi resumen de cuenta”**: para meses viejos donde el banco no deja exportar a Excel, podés dejar el PDF del resumen en la carpeta mensual y el pipeline lo importa.
  - **Importante**: el PDF tiene que ser “texto” (seleccionable). Si es un escaneo (imagen), habría que agregar OCR.
  - **(TODO documentar)**: pasos exactos en Santander Online/APP para bajar `movimientos.xlsx` y/o el PDF del resumen.

- **Tarjeta / Crédito (Santander VISA)**
  - **PDF “Resumen de cuenta VISA”**: se puede dejar el PDF del resumen en la carpeta mensual y el pipeline lo importa.
  - **(TODO documentar)**: pasos exactos para descargar resúmenes viejos (PDF) y el último resumen (si Santander permite Excel).

Si encontrás una forma exacta de descarga para cada fuente (pasos/capturas), este README es el lugar ideal para documentarlo.

---

## Estructura del proyecto

```
tracker-gastos/
├── Gastos/                    # Tus extractos (no se sube a Git)
│   └── 2025-01/              # Una carpeta por mes
├── config/
│   ├── config.json
│   ├── categorias.ejemplo.json
│   └── objetivos.ejemplo.json
├── data/                     # Salidas (no se sube a Git)
├── docs/MAPEO_COLUMNAS.md    # Dónde mapea cada tipo de archivo
├── scripts/
│   ├── run.py                # Ejecuta todo
│   ├── 01_importar.py
│   ├── 02_categorizar.py
│   ├── 03_metricas.py
│   └── debug_categoria.py
└── src/
```

---

## Formatos soportados

Se esperan 3 archivos por mes:
- **Mercado Pago:** extracto con columnas RELEASE_DATE, TRANSACTION_TYPE, TRANSACTION_NET_AMOUNT
- **Débito:** movimientos con Fecha, Descripción, Caja de Ahorro
- **Crédito:** consumos Visa/Master con Fecha, Descripción, Monto en pesos

Si tu banco usa otro formato, ver `docs/MAPEO_COLUMNAS.md` para ajustar el mapeo.

---

## Opciones en config.json

- `periodo_actual`: `null` = usa el mes más reciente. O `"2025-01"` para forzar uno.
- `debug_import`: `true` = el script 01 muestra qué filas omitió del archivo de crédito y por qué.
- `reporte_sin_asignar`: `true` = el script 02 lista las descripciones que no matchearon ninguna categoría.

**debug_categoria.py** — Si un movimiento cae en la categoría equivocada, podés ver qué keyword lo matcheó:
```bash
python scripts/debug_categoria.py "descripción del movimiento"
```

---

## MVP Web (sin IDE, efímero)

Este repo incluye un MVP web (monolito) pensado para que cualquiera suba archivos, procese un período y vea métricas.
La sesión es **efímera**: inputs + outputs se borran automáticamente (TTL).

### Correr local

```bash
pip install -r requirements.txt
python -m uvicorn mvp_web.main:app --host 127.0.0.1 --port 8000
```

Abrir `http://127.0.0.1:8000/`.

### Variables de entorno (útiles para deploy)

- `TG_TTL_SECONDS`: TTL de la sesión (default 3600)
- `TG_MAX_BYTES`: tamaño máximo total de uploads por sesión (default 25MB)
- `TG_MAX_FILES`: cantidad máxima de archivos por sesión (default 30)
- `TG_COOKIE_SECURE`: `1` para cookies secure detrás de HTTPS (default `0`)
- `TG_STORAGE_ROOT`: carpeta base para `storage/` (default `./storage`)

### Deploy en internet (Render / Railway / Fly)

Guía paso a paso: **[docs/DEPLOY_BACKEND.md](docs/DEPLOY_BACKEND.md)**  
Health check: `GET /health`

La landing en Vercel (`landing/`) y el API pueden vivir en dominios distintos: el botón “Try it” debe apuntar a la URL pública del API.

---

## Subir tu fork a GitHub

```bash
git init
git add .
git status
git commit -m "Initial commit"
git remote add origin https://github.com/TU_USUARIO/tracker-gastos.git
git branch -M main
git push -u origin main
```

`Gastos/`, `data/`, `categorias.json` y `objetivos.json` están en `.gitignore` (no se suben).
