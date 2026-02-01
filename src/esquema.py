"""
Esquema estándar de datos. Todos los importadores deben mapear a estas columnas.
"""

# Columnas que tendrá todo archivo estandarizado
COLUMNAS_ESTANDAR = [
    "fecha",           # YYYY-MM-DD
    "descripcion",     # Texto libre del movimiento
    "monto",           # Número (positivo=ingreso, negativo=gasto)
    "origen",          # Archivo de donde provino
    "periodo",         # YYYY-MM para agrupar
]
