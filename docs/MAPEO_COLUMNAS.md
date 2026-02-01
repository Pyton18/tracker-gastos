# Mapeo de columnas por archivo origen

Este documento indica de qué columna/fila proviene cada campo estándar para cada tipo de archivo.
Para cambiar el mapeo, editar `src/importadores.py` en la función indicada.

---

## 1. Mercado Pago (account_statement)

**Función:** `importar_mercadopago()` — líneas 57-90

**Lectura:** Se busca la fila que contiene `RELEASE_DATE` y se usa como encabezado. Luego se accede por nombre de columna.

| Campo estándar | Origen en archivo | Línea |
|----------------|-------------------|-------|
| fecha          | Columna `RELEASE_DATE` | 75 |
| descripcion    | Columna `TRANSACTION_TYPE` | 78 |
| monto          | Columna `TRANSACTION_NET_AMOUNT` | 79 |
| origen         | Fijo: `mercadopago:{nombre_archivo}` | 87 |
| periodo        | Parámetro del período (ej: 2025-12) | 88 |

---

## 2. Débito (movimientos bancarios)

**Función:** `importar_debito()` — líneas 93-133

**Lectura:** Se busca la fila que contiene "Fecha" y "Descripci" como encabezado. Luego se accede por **índice de columna** (iloc). Columnas 0-based.

| Campo estándar | Origen en archivo | Línea |
|----------------|-------------------|-------|
| fecha          | **Columna 1** (iloc[1]) | 110, 116-117 |
| descripcion    | **Columna 3** (iloc[3]) | 111, 121 |
| monto          | **Columna 5** (iloc[5]) o, si vacía, **Columna 6** (iloc[6]) | 112-114, 122 |
| origen         | Fijo: `debito:{nombre_archivo}` | 130 |
| periodo        | Parámetro del período | 131 |

**Nota:** La fecha se hereda si la celda está vacía (se usa la última fecha vista).

---

## 3. Crédito (Visa / consumos)

**Función:** `importar_credito()` — líneas 136+

**Lectura:** Se usa encabezado como Mercado Pago y Débito.
- **Encabezado:** La fila siguiente a la que contiene "Tarjeta de ... Visa Crédito" (por defecto fila 18 del Excel).
- **Columnas por nombre:** Fecha, Descripción, Monto en pesos, Monto en dólares.
- **Stop:** Al encontrar "Subtotal" en Fecha o Descripción — esa fila es la suma de montos y no se importa.

| Campo estándar | Origen en archivo |
|----------------|-------------------|
| fecha          | Columna "Fecha" (DD/MM/YYYY). Se hereda si vacía. |
| descripcion    | Columna "Descripción" |
| monto          | Columna "Monto en pesos" o "Monto en dólares" |
| origen         | Fijo: `credito:{nombre_archivo}` |
| periodo        | Parámetro del período |

**Se omiten:** fila Subtotal, "pago en pesos", descripción vacía, monto=0. La fecha se hereda entre filas cuando está vacía.
