"""
Módulo de Gestión de Portafolio - TradeaYa!
Este archivo administra el estado del portafolio del usuario:
qué acciones posee, cuántas, y a qué precio promedio las compró.
Se comunica con calculos.py para registrar los resultados
de transacciones ya validadas.
"""

# ─────────────────────────────────────────────
# SECCIÓN 1: Inicialización
# ─────────────────────────────────────────────

def crear_portafolio():
    """
    Crea y devuelve un portafolio vacío.
    
    Es el punto de partida cuando un usuario nuevo entra al simulador.
    El frontend o main.py llamará esto una sola vez al inicio de la sesión.
    
    Devuelve:
        dict: Un diccionario vacío listo para recibir posiciones.
    
    Ejemplo de uso:
        mi_portafolio = crear_portafolio()
        >>> {}
    """
    # TU CÓDIGO AQUÍ
    pass


# ─────────────────────────────────────────────
# SECCIÓN 2: Registrar Compra
# ─────────────────────────────────────────────

def registrar_compra(portafolio, simbolo, cantidad, precio_compra):
    """
    Añade o incrementa una posición en el portafolio después de una compra exitosa.
    
    IMPORTANTE: Esta función solo debe llamarse DESPUÉS de que
    validar_transaccion_compra() en calculos.py haya devuelto True.
    Nunca la llames directamente sin validar primero.
    
    Hay dos casos posibles:
    
    CASO A — El usuario NO tiene esa acción todavía:
        Se crea una entrada nueva con la cantidad y el precio de compra tal cual.
    
    CASO B — El usuario YA tiene esa acción:
        Se debe calcular el nuevo precio promedio ponderado.
        Fórmula del promedio ponderado:
        
        nuevo_promedio = ((cantidad_actual * precio_actual_promedio) + (cantidad_nueva * precio_nuevo))
                         / (cantidad_actual + cantidad_nueva)
        
        Ejemplo:
            Tenías: 5 acciones a $170 promedio
            Compras: 5 acciones a $180
            Nuevo promedio: ((5 * 170) + (5 * 180)) / (5 + 5) = $175.00
    
    Parámetros:
        portafolio (dict): El diccionario del portafolio actual.
        simbolo (str): El ticker de la acción. Ej: "AAPL", "TSLA"
        cantidad (int): Cuántas acciones se compraron.
        precio_compra (float): El precio por acción al momento de la compra.
                               Este valor viene directamente del return de
                               validar_transaccion_compra() en calculos.py.
    
    Devuelve:
        dict: El portafolio actualizado.
    
    Ejemplo de uso:
        portafolio = registrar_compra(portafolio, "AAPL", 5, 170.00)
        portafolio = registrar_compra(portafolio, "AAPL", 5, 180.00)
        >>> {"AAPL": {"cantidad": 10, "precio_compra_promedio": 175.00}}
    """
    # TU CÓDIGO AQUÍ
    pass


# ─────────────────────────────────────────────
# SECCIÓN 3: Registrar Venta
# ─────────────────────────────────────────────

def registrar_venta(portafolio, simbolo, cantidad_vendida):
    """
    Reduce o elimina una posición en el portafolio después de una venta exitosa.
    
    IMPORTANTE: Esta función solo debe llamarse DESPUÉS de que
    validar_transaccion_venta() en calculos.py haya devuelto True.
    
    Hay dos casos posibles:
    
    CASO A — El usuario vende MENOS de lo que tiene:
        Solo se reduce la cantidad. El precio promedio NO cambia
        (vender no altera el costo promedio de lo que queda).
        
        Ejemplo:
            Tenías: 10 acciones a $175 promedio
            Vendes: 3 acciones
            Queda:  7 acciones a $175 promedio (sin cambio en precio)
    
    CASO B — El usuario vende TODO lo que tiene:
        Se elimina la entrada completa del diccionario.
        No tiene sentido guardar {"AAPL": {"cantidad": 0, ...}}
        
        Ejemplo:
            Tenías: 3 acciones
            Vendes: 3 acciones
            Resultado: "AAPL" desaparece del portafolio
    
    Parámetros:
        portafolio (dict): El diccionario del portafolio actual.
        simbolo (str): El ticker de la acción. Ej: "AAPL", "TSLA"
        cantidad_vendida (int): Cuántas acciones se vendieron.
    
    Devuelve:
        dict: El portafolio actualizado.
    
    Ejemplo de uso:
        portafolio = registrar_venta(portafolio, "AAPL", 3)
        >>> {"AAPL": {"cantidad": 7, "precio_compra_promedio": 175.00}}
        
        portafolio = registrar_venta(portafolio, "AAPL", 7)
        >>> {}
    """
    # TU CÓDIGO AQUÍ
    pass


# ─────────────────────────────────────────────
# SECCIÓN 4: Consultar Posición
# ─────────────────────────────────────────────

def obtener_posicion(portafolio, simbolo):
    """
    Devuelve los datos de una acción específica dentro del portafolio.
    
    El frontend la usará para mostrarle al usuario cuántas acciones
    tiene de un símbolo particular y a qué precio promedio las compró.
    
    Parámetros:
        portafolio (dict): El diccionario del portafolio actual.
        simbolo (str): El ticker a consultar. Ej: "AAPL"
    
    Devuelve:
        dict: Los datos de esa posición, o None si no existe.
    
    Ejemplo de uso:
        obtener_posicion(portafolio, "AAPL")
        >>> {"cantidad": 7, "precio_compra_promedio": 175.00}
        
        obtener_posicion(portafolio, "NVDA")  # No existe
        >>> None
    """
    # TU CÓDIGO AQUÍ
    # Pista: los diccionarios tienen un método .get() que devuelve
    # None si la clave no existe. Eso es exactamente lo que necesitas.
    pass


# ─────────────────────────────────────────────
# SECCIÓN 5: Valor Total del Portafolio
# ─────────────────────────────────────────────

def calcular_valor_portafolio(portafolio, precios_actuales):
    """
    Calcula el valor de mercado total de todo el portafolio ahora mismo.
    
    Esta es la función más importante para el dashboard del frontend.
    Muestra cuánto vale en dólares todo lo que el usuario tiene,
    usando los precios actuales (no los de compra).
    
    Parámetros:
        portafolio (dict): El diccionario del portafolio actual.
        precios_actuales (dict): Diccionario con los precios vigentes
                                 de cada acción que proviene del backend.
        
        Formato esperado de precios_actuales:
        {
            "AAPL": 195.30,
            "TSLA": 185.50,
            "NVDA": 430.00
        }
    
    Devuelve:
        float: El valor total en dólares del portafolio a precios actuales.
    
    Lógica:
        Para cada acción en el portafolio:
            valor_posicion = cantidad * precio_actual
        Sumar todos los valores_posicion.
    
    MANEJO DE CASO ESPECIAL:
        Si una acción del portafolio no aparece en precios_actuales
        (el backend no trajo ese precio), debes ignorarla y continuar.
        No rompas el programa por un precio faltante.
    
    Ejemplo de uso:
        portafolio = {"AAPL": {"cantidad": 10, "precio_compra_promedio": 175},
                      "TSLA": {"cantidad": 3,  "precio_compra_promedio": 220}}
        precios    = {"AAPL": 195.30, "TSLA": 185.50}
        
        calcular_valor_portafolio(portafolio, precios)
        >>> 2509.50   # (10 * 195.30) + (3 * 185.50)
    """
    # TU CÓDIGO AQUÍ
    # Pista: empieza con valor_total = 0.0
    # Luego recorre el portafolio con un for y ve sumando.
    pass

portafolio = {
    "AAPL": {
        "cantidad": 10,
        "precio_compra_promedio": 175.50  # precio promedio ponderado
    },
    "TSLA": {
        "cantidad": 5,
        "precio_compra_promedio": 220.00
    }
}
