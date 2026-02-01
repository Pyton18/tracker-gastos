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
    """Devuelve 'mercadopago' | 'debito' | 'credito' | None."""
    name = ruta.name.lower()
    if "account_statement" in name or "mercadopago" in name:
        return "mercadopago"
    if "movimientos" in name or "debito" in name or "cuenta" in name:
        return "debito"
    if "visa" in name or "consumos" in name or "credito" in name or "master" in name:
        return "credito"
    return None


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


def importar_archivo(ruta: Path, periodo: str, debug: bool = False) -> pd.DataFrame:
    """Despacha al importador correcto según el tipo de archivo."""
    tipo = _detectar_tipo_archivo(ruta)
    if tipo == "mercadopago":
        return importar_mercadopago(ruta, periodo)
    if tipo == "debito":
        return importar_debito(ruta, periodo)
    if tipo == "credito":
        return importar_credito(ruta, periodo, debug=debug)
    return pd.DataFrame()
