"""
logic/calculos.py - TradeaYa!
Reglas de negocio puras: horario, comisiones, validaciones de compra/venta.
No depende de Streamlit ni de la base de datos.

REGLAS IMPLEMENTADAS
────────────────────
• Horario de mercado : Lunes–Viernes, 9:30–16:00 EST
  (horas ampliadas intencionalmente para testing; ver comentarios en mercado_abierto)
• Comisión broker    : 0.5 % por transacción
• Latencia máxima    : 60 segundos desde que se obtuvo el precio
• Validación compra  : saldo suficiente + mercado abierto + precio fresco
• Validación venta   : acción en portafolio + cantidad suficiente + mercado abierto + precio fresco
• Rendimiento        : ((precio_actual - precio_compra) / precio_compra) × 100
"""

from datetime import datetime
import time

import pytz


# ─────────────────────────────────────────────────────────
# SECCIÓN 1: Horario de mercado
# ─────────────────────────────────────────────────────────

def mercado_abierto() -> bool:
    """
    Verifica si el mercado de EE. UU. está operativo.
    Producción real: Lunes a Viernes de 9:30 a 16:00 Zona Horaria de Nueva York.

    NOTA DE TESTING: weekday < 7 (siempre True) y horas 01:00–23:59
    permiten operar cualquier día y hora. Para producción cambiar:
        weekday < 7  →  weekday < 5
        hour=1       →  hour=9,  minute=30
        hour=23      →  hour=16, minute=0
    """
    tz_ny     = pytz.timezone("America/New_York")
    ahora_ny  = datetime.now(tz_ny)

    es_dia_habil   = ahora_ny.weekday() < 5 ########
    hora_apertura  = ahora_ny.replace(hour=9,  minute=30,  second=0, microsecond=0)
    hora_cierre    = ahora_ny.replace(hour=16, minute=0, second=0, microsecond=0) ##############

    return es_dia_habil and (hora_apertura <= ahora_ny <= hora_cierre)


# ─────────────────────────────────────────────────────────
# SECCIÓN 2: Comisión del broker
# ─────────────────────────────────────────────────────────

COMISION_PORCENTAJE = 0.005  # 0.5 %

def calcular_comision(monto_total: float) -> float:
    """Devuelve el monto de comisión para una operación."""
    return monto_total * COMISION_PORCENTAJE


# ─────────────────────────────────────────────────────────
# SECCIÓN 3: Frescura del precio
# ─────────────────────────────────────────────────────────

LATENCIA_MAXIMA_SEGUNDOS = 60  # Reducido de 120 a 60 s (sincronizado con auto-refresh)

def es_precio_valido(timestamp_precio: float) -> bool:
    """True si el precio fue obtenido hace menos de LATENCIA_MAXIMA_SEGUNDOS."""
    return (time.time() - timestamp_precio) <= LATENCIA_MAXIMA_SEGUNDOS


# ─────────────────────────────────────────────────────────
# SECCIÓN 4: Cálculos de montos
# ─────────────────────────────────────────────────────────

def calcular_monto_a_pagar(precio_actual: float, cantidad: int) -> float:
    """Monto total a descontar del saldo al comprar (precio × cantidad + comisión)."""
    monto_bruto = precio_actual * cantidad
    return monto_bruto + calcular_comision(monto_bruto)


def calcular_monto_a_recibir(precio_actual: float, cantidad: int) -> float:
    """Monto total a acreditar al saldo al vender (precio × cantidad − comisión)."""
    monto_bruto = precio_actual * cantidad
    return monto_bruto - calcular_comision(monto_bruto)


def calcular_rendimiento(precio_compra: float, precio_actual: float) -> float:
    """Rendimiento en % respecto al precio de compra. Devuelve 0.0 si precio_compra es 0."""
    if precio_compra == 0:
        return 0.0
    return ((precio_actual - precio_compra) / precio_compra) * 100


# ─────────────────────────────────────────────────────────
# SECCIÓN 5: Validación de compra
# ─────────────────────────────────────────────────────────

def validar_transaccion_compra(
    saldo_actual: float,
    precio_actual: float,
    cantidad: int,
    timestamp_precio: float,
) -> tuple[bool, str, float, float | None]:
    """
    Valida si una compra puede ejecutarse.

    Devuelve: (éxito, mensaje, saldo_resultante, precio_compra)
    • éxito=False  →  No hay cambios, se determina el faltante, permanece saldo_actual, precio_compra es None.
    • éxito=True   →  nuevo_saldo es el saldo después de la compra.
    """
    if not mercado_abierto():
        return False, "Mercado cerrado. Solo se permite visualización.", saldo_actual, None

    if not es_precio_valido(timestamp_precio):
        return False, "Precio desactualizado. Espera la próxima actualización.", saldo_actual, None

    monto_a_pagar = calcular_monto_a_pagar(precio_actual, cantidad)

    if saldo_actual >= monto_a_pagar:
        nuevo_saldo = saldo_actual - monto_a_pagar
        return True, f"Compra exitosa. Nuevo saldo: ${nuevo_saldo:.2f}", nuevo_saldo, precio_actual

    falta = monto_a_pagar - saldo_actual
    return False, f"Saldo insuficiente. Te faltan ${falta:.2f}.", saldo_actual, None


# ─────────────────────────────────────────────────────────
# SECCIÓN 6: Validación de venta
# ─────────────────────────────────────────────────────────

def validar_transaccion_venta(
    portafolio: dict,
    simbolo: str,
    cantidad: int,
    precio_actual: float,
    timestamp_precio: float,
) -> tuple[bool, str, float]:
    """
    Valida si una venta puede ejecutarse.

    Devuelve: (éxito, mensaje, monto_a_recibir)
    • éxito=False  →  monto_a_recibir es 0.0
    • éxito=True   →  monto_a_recibir se calcula y devuelve
    """
    if not mercado_abierto():
        return False, "Mercado cerrado. Solo se permite visualización.", 0.0

    if not es_precio_valido(timestamp_precio):
        return False, "Precio desactualizado. Espera la próxima actualización.", 0.0

    if simbolo not in portafolio:
        return False, f"No tienes acciones de {simbolo} en tu portafolio.", 0.0

    cantidad_poseida = portafolio[simbolo]["cantidad"]
    if cantidad > cantidad_poseida:
        return False, f"No puedes vender {cantidad}. Solo posees {cantidad_poseida}.", 0.0

    monto_a_recibir = calcular_monto_a_recibir(precio_actual, cantidad)
    return True, f"Venta exitosa. Recibes: ${monto_a_recibir:.2f}", monto_a_recibir