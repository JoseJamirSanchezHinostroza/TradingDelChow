"""
logic/portafolio.py - TradeaYa!
Gestión en memoria del portafolio del usuario: altas, bajas y consultas.
No depende de la base de datos ni de Streamlit.
"""


# ─────────────────────────────────────────────────────────
# SECCIÓN 1: Crear portafolio vacío
# ─────────────────────────────────────────────────────────

def crear_portafolio() -> dict:
    """Devuelve un diccionario: portafolio vacío. Se llama una vez al iniciar sesión."""
    return {}


# ─────────────────────────────────────────────────────────
# SECCIÓN 2: Registrar compra
# ─────────────────────────────────────────────────────────

def registrar_compra(portafolio: dict, simbolo: str, cantidad: int, precio: float) -> dict:
    """
    Actualiza el portafolio tras una compra exitosa. Utiliza:
    -Estado actual del portafolio (diccionario)
    -Ticker de la acción (string)
    -Cantidad que se compra (integer)
    -Precio de compra (float)

    • Acción nueva     → Crea una entrada en el diccionario con el símbolo y le asigna su cantidad-precio.
    • Acción existente → A partir de la cantidad-precio que ya había se calcula el precio promedio ponderado. Se asigna nuevo cantidad-precio.

    Fórmula: nuevo_prom = (cant_actual × prom_actual + cant_nueva × precio_nuevo)
                          / (cant_actual + cant_nueva)
    """
    if simbolo not in portafolio: # Acción nueva que no pertenece al portafolio
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
    Actualiza el portafolio tras una venta exitosa. Utiliza:
    -Estado actual del portafolio (diccionario)
    -Ticker de la acción (string)
    -Cantidad que se compra (integer)

    • No existe el Ticker en el portafolio → No se vende nada.
    • Venta parcial → Reduce la cantidad (precio promedio no cambia).
    • Venta total   → Elimina el Ticker del diccionario.
    """
    if simbolo not in portafolio: # No hay acción en el portafolio
        return portafolio  # No debería ocurrir si se validó antes

    if cantidad >= portafolio[simbolo]["cantidad"]: # Venta total
        del portafolio[simbolo]
    else: # Venta parcial
        portafolio[simbolo]["cantidad"] -= cantidad

    return portafolio


# ─────────────────────────────────────────────────────────
# SECCIÓN 4: Consultar una posición
# ─────────────────────────────────────────────────────────

def obtener_posicion(portafolio: dict, simbolo: str) -> dict | None:
    """Devuelve los datos de una acción específica dentro del portafolio, o None si no está en este."""
    return portafolio.get(simbolo)


# ─────────────────────────────────────────────────────────
# SECCIÓN 5: Valor total del portafolio
# ─────────────────────────────────────────────────────────

def calcular_valor_portafolio(portafolio: dict, precios_actuales: dict) -> float:
    """
    Calcula el valor total en dólares del portafolio al precio más actual (float).
    Las acciones sin precio disponible se ignoran sin interrumpir el cálculo.

    precios_actuales: { "AAPL": 195.30, "TSLA": 185.50, ... }
    """
    total = sum( # Función sum() para sumar todos los valores dentro del ()
        datos["cantidad"] * precios_actuales[simbolo] # Nº acciones*cantidad
        for simbolo, datos in portafolio.items() # Iteración sobre cada acción del portafolio
        if simbolo in precios_actuales # Toma el dato sólo si el símbolo cuenta con un precio válido
    )
    return round(total, 2) # Redondeo a 2 decimales
