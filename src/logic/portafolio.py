"""
logic/portafolio.py - TradeaYa!
Gestión en memoria del portafolio del usuario: altas, bajas y consultas.
No depende de la base de datos ni de Streamlit.
"""


# ─────────────────────────────────────────────────────────
# SECCIÓN 1: Crear portafolio vacío
# ─────────────────────────────────────────────────────────

def crear_portafolio() -> dict:
    """Devuelve un portafolio vacío. Se llama una vez al iniciar sesión."""
    return {}


# ─────────────────────────────────────────────────────────
# SECCIÓN 2: Registrar compra
# ─────────────────────────────────────────────────────────

def registrar_compra(portafolio: dict, simbolo: str, cantidad: int, precio: float) -> dict:
    """
    Actualiza el portafolio tras una compra exitosa.

    • Acción nueva     → la agrega directamente.
    • Acción existente → recalcula el precio promedio ponderado.

    Fórmula: nuevo_prom = (cant_actual × prom_actual + cant_nueva × precio_nuevo)
                          / (cant_actual + cant_nueva)
    """
    if simbolo not in portafolio:
        portafolio[simbolo] = {"cantidad": cantidad, "precio_compra_promedio": precio}
    else:
        cant_actual  = portafolio[simbolo]["cantidad"]
        prom_actual  = portafolio[simbolo]["precio_compra_promedio"]
        nueva_cant   = cant_actual + cantidad
        nuevo_prom   = ((cant_actual * prom_actual) + (cantidad * precio)) / nueva_cant

        portafolio[simbolo]["cantidad"]               = nueva_cant
        portafolio[simbolo]["precio_compra_promedio"] = round(nuevo_prom, 4)

    return portafolio


# ─────────────────────────────────────────────────────────
# SECCIÓN 3: Registrar venta
# ─────────────────────────────────────────────────────────

def registrar_venta(portafolio: dict, simbolo: str, cantidad: int) -> dict:
    """
    Actualiza el portafolio tras una venta exitosa.

    • Venta parcial → reduce la cantidad (precio promedio no cambia).
    • Venta total   → elimina la posición.
    """
    if simbolo not in portafolio:
        return portafolio  # No debería ocurrir si se validó antes

    if cantidad >= portafolio[simbolo]["cantidad"]:
        del portafolio[simbolo]
    else:
        portafolio[simbolo]["cantidad"] -= cantidad

    return portafolio


# ─────────────────────────────────────────────────────────
# SECCIÓN 4: Consultar una posición
# ─────────────────────────────────────────────────────────

def obtener_posicion(portafolio: dict, simbolo: str) -> dict | None:
    """Devuelve los datos de una acción específica, o None si no está en el portafolio."""
    return portafolio.get(simbolo)


# ─────────────────────────────────────────────────────────
# SECCIÓN 5: Valor total del portafolio
# ─────────────────────────────────────────────────────────

def calcular_valor_portafolio(portafolio: dict, precios_actuales: dict) -> float:
    """
    Calcula el valor total en dólares del portafolio al precio de hoy.
    Las acciones sin precio disponible se ignoran sin interrumpir el cálculo.

    precios_actuales: { "AAPL": 195.30, "TSLA": 185.50, ... }
    """
    total = sum(
        datos["cantidad"] * precios_actuales[simbolo]
        for simbolo, datos in portafolio.items()
        if simbolo in precios_actuales
    )
    return round(total, 2)
