"""
Módulo de Gestión de Portafolio - TradeaYa!
Administra el estado del portafolio: qué acciones tienes,
cuántas, y a qué precio promedio las compraste.
"""

# ─────────────────────────────────────────────────────────
# SECCIÓN 1: Crear portafolio vacío
# ─────────────────────────────────────────────────────────

def crear_portafolio():
    """
    Devuelve un portafolio vacío.
    Se llama una sola vez al iniciar la sesión del usuario.
    """
    return {}


# ─────────────────────────────────────────────────────────
# SECCIÓN 2: Registrar compra en el portafolio
# ─────────────────────────────────────────────────────────

def registrar_compra(portafolio, simbolo, cantidad, precio_compra):
    """
    Actualiza el portafolio después de una compra exitosa.

    CASO A - Acción nueva: la agrega directo.
    CASO B - Acción existente: recalcula el precio promedio ponderado.

    Fórmula promedio ponderado:
        nuevo_prom = ((cant_actual * prom_actual) + (cant_nueva * precio_nuevo))
                     / (cant_actual + cant_nueva)
    """
    if simbolo not in portafolio:
        # CASO A: primera vez que compras esta acción
        portafolio[simbolo] = {
            "cantidad": cantidad_comprada,
            "precio_compra_promedio": precio_compra
        }
    else:
        # CASO B: ya tienes esta acción, recalcula el promedio
        cantidad_poseida   = portafolio[simbolo]["cantidad"]
        prom_actual   = portafolio[simbolo]["precio_compra_promedio"]

        nueva_cantidad = cantidad_poseida + cantidad_comprada
        nuevo_promedio = ((cantidad_poseida * prom_actual) + (cantidad_comprada * precio_compra)) / nueva_cantidad

        portafolio[simbolo]["cantidad"]              = nueva_cantidad
        portafolio[simbolo]["precio_compra_promedio"] = round(nuevo_promedio, 4)

    return portafolio


# ─────────────────────────────────────────────────────────
# SECCIÓN 3: Registrar venta
# ─────────────────────────────────────────────────────────

def registrar_venta(portafolio, simbolo, cantidad_vendida):
    """
    Actualiza el portafolio después de una venta exitosa.

    CASO A - Vende menos de lo que tiene: reduce cantidad,
             el precio promedio NO cambia.
    CASO B - Vende todo: elimina la entrada del diccionario.
    """
    if simbolo not in portafolio:
        return portafolio  # No debería pasar si validaste antes, pero por seguridad

    cant_actual = portafolio[simbolo]["cantidad"]

    if cantidad_vendida >= cant_actual:
        # CASO B: vendió todo, elimina la posición
        del portafolio[simbolo]
    else:
        # CASO A: vendió parcial, solo reduce cantidad
        portafolio[simbolo]["cantidad"] -= cantidad_vendida

    return portafolio


# ─────────────────────────────────────────────────────────
# SECCIÓN 4: Consultar una posición
# ─────────────────────────────────────────────────────────

def obtener_posicion(portafolio, simbolo):
    """
    Devuelve los datos de una acción específica.
    Devuelve None si no la tienes.

    El frontend usa esto para mostrar cuánto tienes de cada acción.
    """
    return portafolio.get(simbolo, None)


# ─────────────────────────────────────────────────────────
# SECCIÓN 5: Valor total del portafolio
# ─────────────────────────────────────────────────────────

def calcular_valor_portafolio(portafolio, precios_actuales):
    """
    Calcula cuánto vale en dólares todo tu portafolio HOY.
    Usa precios actuales, no los de compra.

    precios_actuales viene del backend así:
        {"AAPL": 195.30, "TSLA": 185.50}

    Si una acción del portafolio no tiene precio disponible,
    se ignora sin romper el programa.
    """
    valor_total = 0.0

    for simbolo, datos in portafolio.items():
        precio_hoy = precios_actuales.get(simbolo)   # None si no está disponible
        if precio_hoy is not None:
            valor_total += datos["cantidad"] * precio_hoy

    return round(valor_total, 2)
