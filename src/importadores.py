"""
Importadores específicos por tipo de archivo.
Cada uno mapea al esquema estándar: fecha, descripcion, monto, origen, periodo.
"""
import re
from pathlib import Path
from datetime import datetime

import pandas as pd


def _parsear_fecha(val, formatos=None):
    """Intenta parsear fecha en varios formatos."""
    if pd.isna(val) or val == "" or val == "-":
        return None
    val = str(val).strip()
    formatos = formatos or ["%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formatos:
        try:
            return datetime.strptime(val[:10], fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return None


def _parsear_monto(val):
    """Convierte string de monto (1.234,56 o 1234.56) a float."""
    if pd.isna(val) or val == "":
        return 0.0
    s = str(val).strip()
    s = s.replace("$", "").replace("U$S", "").replace(" ", "")
    # Formato europeo: 1.234,56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(".", "").replace(",", ".") if "," in s else s
    try:
        return float(s)
    except ValueError:
        return 0.0


def _detectar_tipo_archivo(ruta: Path) -> str:
    """Devuelve 'mercadopago' | 'debito' | 'credito' | 'debito_pdf' | 'credito_pdf' | None."""
    name = ruta.name.lower()
    suf = ruta.suffix.lower()

    if suf == ".pdf":
        try:
            # En algunos PDFs el contenido de "movimientos" aparece recién en páginas 2-3
            texto = _leer_pdf_texto(ruta, max_paginas=3).lower()
        except Exception:
            texto = ""
        # Santander "Mi resumen de cuenta" (cuenta / débito)
        if "mi resumen de cuenta" in texto or "movimientos en pesos" in texto:
            return "debito_pdf"
        # Santander VISA resumen
        if "resumen de cuenta" in texto and "visa" in texto:
            return "credito_pdf"
        return None

    if "account_statement" in name or "mercadopago" in name:
        return "mercadopago"
    if "movimientos" in name or "debito" in name or "cuenta" in name:
        return "debito"
    if "visa" in name or "consumos" in name or "credito" in name or "master" in name:
        return "credito"
    return None


def _leer_pdf_texto(ruta: Path, max_paginas: int | None = None) -> str:
    """
    Extrae texto de un PDF (no OCR).
    Requiere PDF con texto seleccionable.
    """
    import pdfplumber

    chunks: list[str] = []
    with pdfplumber.open(ruta) as pdf:
        paginas = pdf.pages if max_paginas is None else pdf.pages[:max_paginas]
        for p in paginas:
            t = p.extract_text() or ""
            if t:
                chunks.append(t)
    return "\n".join(chunks)


def importar_mercadopago(ruta: Path, periodo: str) -> pd.DataFrame:
    """Importa extracto de Mercado Pago (account_statement)."""
    df_raw = pd.read_excel(ruta, header=None)
    # Buscar fila con RELEASE_DATE
    header_row = None
    for i, row in df_raw.iterrows():
        if "RELEASE_DATE" in str(row.values):
            header_row = int(i)
            break
    if header_row is None:
        return pd.DataFrame()

    df = pd.read_excel(ruta, header=header_row)
    df = df.dropna(subset=["RELEASE_DATE"], how="all")
    df = df[df["RELEASE_DATE"].astype(str).str.match(r"\d{2}[-/]\d{2}[-/]\d{4}", na=False)]

    rows = []
    for _, r in df.iterrows():
        fecha = _parsear_fecha(r.get("RELEASE_DATE"))
        if not fecha:
            continue
        desc = str(r.get("TRANSACTION_TYPE", "") or "")
        monto = _parsear_monto(r.get("TRANSACTION_NET_AMOUNT", 0))

        rows.append({
            "fecha": fecha,
            "descripcion": desc[:500],
            "monto": monto,
            "origen": f"mercadopago:{ruta.name}",
            "periodo": periodo,
        })
    return pd.DataFrame(rows)


def importar_debito(ruta: Path, periodo: str) -> pd.DataFrame:
    """Importa extracto de cuenta bancaria (movimientos)."""
    df = pd.read_excel(ruta, header=None)
    header_row = None
    for i, row in df.iterrows():
        if "Fecha" in str(row.values) and "Descripci" in str(row.values):
            header_row = int(i)
            break
    if header_row is None:
        return pd.DataFrame()

    df = pd.read_excel(ruta, header=header_row)

    rows = []
    fecha_ultima = None
    for _, r in df.iterrows():
        fecha_val = r.iloc[1] if len(r) > 1 else None
        desc_val = r.iloc[3] if len(r) > 3 else ""
        monto_val = r.iloc[5] if len(r) > 5 else None
        if (pd.isna(monto_val) or monto_val == 0) and len(r) > 6:
            monto_val = r.iloc[6]

        if pd.notna(fecha_val) and str(fecha_val).strip():
            fecha_ultima = _parsear_fecha(str(fecha_val).split(" ")[0])
        if not fecha_ultima:
            continue

        desc = str(desc_val or "")[:500]
        monto = _parsear_monto(monto_val or 0)
        rows.append({
            "fecha": fecha_ultima,
            "descripcion": desc,
            "monto": monto,
            "origen": f"debito:{ruta.name}",
            "periodo": periodo,
        })
    return pd.DataFrame(rows)


def importar_credito(ruta: Path, periodo: str, debug: bool = False) -> pd.DataFrame:
    """
    Importa extracto de tarjeta de crédito (Visa/Master consumos).
    Encabezado: fila que contiene Fecha, Descripción, Monto... — la que viene después de "Tarjeta de ... Visa Crédito".
    Stop: al encontrar "Subtotal" en Fecha o Descripción (fila de suma, no es un gasto).
    """
    df_raw = pd.read_excel(ruta, header=None)

    # Buscar encabezado: la fila siguiente a "Tarjeta de ... Visa Crédito" o fila 18 (índice 17) por defecto
    header_row = 17
    for i, row in df_raw.iterrows():
        texto = " ".join(str(x) for x in row.values)
        if "Tarjeta de" in texto and ("Visa" in texto or "Credito" in texto or "Crédito" in texto):
            header_row = int(i) + 1
            break

    df = pd.read_excel(ruta, header=header_row)

    # Mapeo flexible por nombre (puede variar por tildes/espacios)
    col_fecha = next((c for c in df.columns if "fecha" in str(c).lower()), None)
    col_desc = next((c for c in df.columns if "descripci" in str(c).lower()), None)
    col_monto_pesos = next((c for c in df.columns if "monto" in str(c).lower() and "peso" in str(c).lower()), None)
    col_monto_usd = next((c for c in df.columns if "monto" in str(c).lower() and "dolar" in str(c).lower()), None)

    if not all([col_fecha, col_desc, col_monto_pesos]):
        if debug:
            print(f"  [DEBUG crédito] Columnas no encontradas. Disponibles: {list(df.columns)}")
        return pd.DataFrame()

    rows = []
    skipped = []
    fecha_ultima = None

    for i, r in df.iterrows():
        fecha_val = r.get(col_fecha)
        desc_val = r.get(col_desc)
        monto_pesos = r.get(col_monto_pesos)
        monto_usd = r.get(col_monto_usd) if col_monto_usd else None

        # STOP: fila Subtotal (suma de montos) — no es un gasto
        texto_fecha = str(fecha_val or "")
        texto_desc = str(desc_val or "")
        if "Subtotal" in texto_fecha or "Subtotal" in texto_desc:
            if debug:
                skipped.append((i, texto_desc[:60] or texto_fecha[:60], "fila Subtotal (stop)"))
            break

        # Omitir pagos de tarjeta (no son consumos)
        desc = str(desc_val or "").strip() if pd.notna(desc_val) else ""
        if "pago en pesos" in desc.lower() or "pago de tarjeta" in desc.lower():
            if debug:
                skipped.append((i, desc[:60], "pago de tarjeta"))
            continue

        # Descripción vacía: probablemente celda combinada o fila inválida — omitir
        if not desc:
            if debug:
                skipped.append((i, "", "descripción vacía"))
            continue

        # Omitir filas de encabezado repetido
        if "Fecha" in desc or "Descripci" in desc:
            continue

        # Fecha: usar la de la fila o heredar la anterior (pandas puede leer fechas como datetime)
        if pd.notna(fecha_val):
            if hasattr(fecha_val, "strftime"):
                fecha_ultima = fecha_val.strftime("%Y-%m-%d")
            elif str(fecha_val).strip() and re.match(r"\d{1,2}/\d{1,2}/\d{4}", str(fecha_val).strip()):
                fecha_ultima = _parsear_fecha(str(fecha_val).strip())
        if not fecha_ultima:
            if debug:
                skipped.append((i, desc[:60], "sin fecha previa"))
            continue

        monto = _parsear_monto(monto_pesos) if pd.notna(monto_pesos) and str(monto_pesos).strip() else _parsear_monto(monto_usd) if pd.notna(monto_usd) and str(monto_usd).strip() else 0
        if monto == 0:
            if debug:
                skipped.append((i, desc[:60], f"monto=0"))
            continue

        monto = -abs(monto)

        rows.append({
            "fecha": fecha_ultima,
            "descripcion": desc[:500],
            "monto": monto,
            "origen": f"credito:{ruta.name}",
            "periodo": periodo,
        })

    if debug and skipped:
        print(f"\n  [DEBUG crédito] Filas omitidas ({len(skipped)}):")
        for fila, desc, motivo in skipped:
            print(f"    Fila {fila}: {desc!r} -> {motivo}")
    return pd.DataFrame(rows)


_MESES_ES = {
    "ene": 1,
    "enero": 1,
    "feb": 2,
    "febrero": 2,
    "mar": 3,
    "marzo": 3,
    "abr": 4,
    "abril": 4,
    "may": 5,
    "mayo": 5,
    "jun": 6,
    "junio": 6,
    "jul": 7,
    "julio": 7,
    "ago": 8,
    "agosto": 8,
    "sep": 9,
    "sept": 9,
    "septiembre": 9,
    "oct": 10,
    "octubre": 10,
    "nov": 11,
    "noviembre": 11,
    "dic": 12,
    "diciem": 12,   # "Diciem." en resúmenes
    "diciembre": 12,
}


def _parsear_monto_ar(s: str) -> float | None:
    """
    Parse monto AR con miles '.' y decimales ',' y posible sufijo '-'.
    Ej: '16.957,96' o '89.898,08-' o '-$ 36.400,00'
    """
    if not s:
        return None
    t = str(s).strip()
    neg = False
    if t.endswith("-"):
        neg = True
        t = t[:-1].strip()
    t = t.replace("U$S", "").replace("$", "").replace(" ", "")
    # manejar prefijo - (ej: -$ 36.400,00)
    if t.startswith("-"):
        neg = True
        t = t[1:].strip()
    # 1.234,56 -> 1234.56
    t = t.replace(".", "").replace(",", ".")
    try:
        val = float(t)
        return -abs(val) if neg else val
    except ValueError:
        return None


def importar_debito_pdf(ruta: Path, periodo: str) -> pd.DataFrame:
    """
    Importa PDF 'Mi resumen de cuenta' (Santander).
    Espera sección "Movimientos en pesos" con tabla:
      Fecha Comprobante Movimiento ... Saldo
    """
    texto = _leer_pdf_texto(ruta)
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]

    # encontrar donde arranca la tabla
    start = None
    for i, l in enumerate(lineas):
        if l.lower().startswith("movimientos en pesos"):
            start = i
            break
    if start is None:
        return pd.DataFrame()

    movimientos: list[dict] = []
    fecha_actual: str | None = None
    desc_parts: list[str] = []
    monto_actual: float | None = None

    date_re = re.compile(r"^(?P<d>\d{2})/(?P<m>\d{2})/(?P<y>\d{2})\b")
    money_re = re.compile(r"(?P<sign>-?\$)\s*(?P<num>\d{1,3}(?:\.\d{3})*,\d{2})")

    def flush():
        nonlocal desc_parts, monto_actual, fecha_actual
        if fecha_actual and monto_actual is not None and desc_parts:
            descripcion = " ".join(desc_parts).strip()
            movimientos.append({
                "fecha": fecha_actual,
                "descripcion": descripcion[:500],
                "monto": monto_actual,
                "origen": f"debito_pdf:{ruta.name}",
                "periodo": periodo,
            })
        desc_parts = []
        monto_actual = None

    for l in lineas[start:]:
        # nueva fila si arranca con fecha dd/mm/yy
        m = date_re.match(l)
        if m:
            flush()
            d, mo, y = int(m.group("d")), int(m.group("m")), int(m.group("y"))
            fecha_actual = f"20{y:02d}-{mo:02d}-{d:02d}"
            # la línea tiene el comienzo del movimiento + posible monto
            resto = l[m.end():].strip()
            if resto:
                desc_parts.append(resto)
            # monto: tomar el primer $... que aparezca en la línea (suele ser el movimiento, el saldo viene después)
            mm = money_re.search(l)
            if mm:
                raw = f"{mm.group('sign')} {mm.group('num')}"
                monto_actual = _parsear_monto_ar(raw)
            continue

        # líneas de continuación: suelen ser parte de la descripción
        if fecha_actual:
            # si aparece un monto en continuación y todavía no lo capturamos, usarlo
            if monto_actual is None:
                mm = money_re.search(l)
                if mm:
                    raw = f"{mm.group('sign')} {mm.group('num')}"
                    monto_actual = _parsear_monto_ar(raw)
                    # remover el monto del texto para que no quede duplicado en descripcion
                    l = money_re.sub("", l).strip()
            if l:
                # cortar ruidos frecuentes
                if l.startswith("-- ") and " of " in l:
                    continue
                desc_parts.append(l)

    flush()

    # normalizar: en el PDF los débitos ya vienen con -$; los créditos con $.
    return pd.DataFrame(movimientos)


def importar_credito_pdf(ruta: Path, periodo: str) -> pd.DataFrame:
    """
    Importa PDF resumen VISA Santander.
    Toma consumos (no pagos) y los exporta como montos negativos.
    """
    texto = _leer_pdf_texto(ruta)
    lineas = [l.strip() for l in texto.splitlines() if l.strip()]

    rows: list[dict] = []
    year: int | None = None
    month: int | None = None

    # ejemplo:
    # 26 Enero 05 000001 * AUBASA ... 16.957,96
    # 08 000001 K AUTOPISTAS ... 6.851,17
    re_full = re.compile(r"^(?P<yy>\d{2})\s+(?P<mes>[A-Za-z\.]+)\s+(?P<dd>\d{2})\s+(?P<rest>.+)$")
    re_cont = re.compile(r"^(?P<dd>\d{2})\s+(?P<rest>.+)$")
    re_amount_tail = re.compile(r"(?P<num>\d{1,3}(?:\.\d{3})*,\d{2}-?)\s*$")

    for l in lineas:
        low = l.lower()
        if "total consumos" in low:
            break
        if "su pago" in low or "pago en pesos" in low:
            continue
        # saltar líneas claramente no-movimientos
        if low.startswith("santander") or "resumen de cuenta" in low or low.startswith("el presente es copia"):
            continue

        m = re_full.match(l)
        if m:
            year = 2000 + int(m.group("yy"))
            mes_raw = m.group("mes").lower().replace(".", "")
            month = _MESES_ES.get(mes_raw)
            dd = int(m.group("dd"))
            rest = m.group("rest").strip()
        else:
            m2 = re_cont.match(l)
            if not m2 or year is None or month is None:
                continue
            dd = int(m2.group("dd"))
            rest = m2.group("rest").strip()

        if year is None or month is None:
            continue

        # monto: último número estilo AR al final de la línea
        ma = re_amount_tail.search(rest)
        if not ma:
            continue
        monto = _parsear_monto_ar(ma.group("num"))
        if monto is None:
            continue
        # los consumos deben ser gasto (negativo)
        monto = -abs(monto)

        desc = re_amount_tail.sub("", rest).strip()
        # limpiar cosas típicas: prefijos con códigos, asteriscos, letras de referencia
        desc = re.sub(r"^[0-9]{3,}\s+", "", desc).strip()
        desc = desc.lstrip("*").strip()

        fecha = f"{year:04d}-{month:02d}-{dd:02d}"
        rows.append({
            "fecha": fecha,
            "descripcion": desc[:500],
            "monto": monto,
            "origen": f"credito_pdf:{ruta.name}",
            "periodo": periodo,
        })

    return pd.DataFrame(rows)


def importar_archivo(ruta: Path, periodo: str, debug: bool = False) -> pd.DataFrame:
    """Despacha al importador correcto según el tipo de archivo."""
    tipo = _detectar_tipo_archivo(ruta)
    if tipo == "mercadopago":
        return importar_mercadopago(ruta, periodo)
    if tipo == "debito":
        return importar_debito(ruta, periodo)
    if tipo == "credito":
        return importar_credito(ruta, periodo, debug=debug)
    if tipo == "debito_pdf":
        return importar_debito_pdf(ruta, periodo)
    if tipo == "credito_pdf":
        return importar_credito_pdf(ruta, periodo)
    return pd.DataFrame()
