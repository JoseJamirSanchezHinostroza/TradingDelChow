"""
logic/sesion.py - TradeaYa!
Unión de calculos.py y portafolio.py en un único objeto, para ello importa sus funciones.
El FrontEnd no utiliza toda la sección logic; solo necesita de la clase SesionTrading.
"""

from datetime import datetime # Manejo fechas-horas

from logic.calculos import (
    validar_transaccion_compra,
    validar_transaccion_venta,
    calcular_rendimiento,
)
from logic.portafolio import (
    crear_portafolio,
    registrar_compra,
    registrar_venta,
    calcular_valor_portafolio,
)


class SesionTrading:
    """
    Cada vez que un usuario entra a la app, se crea una instancia de esta clase.
    Representa la sesión activa de un usuario, cuya cuenta inicia con 100.000 dólares.

    Mantiene en memoria:
        • saldo       – Dinero disponible para operar
        • portafolio  – Acciones (Tickers) actuales con su respectivo precio promedio
        • historial   – Lista de operaciones realizadas en la sesión presente.
        
    Define funciones de compra, venta, resumen y registro en el historial.
    """

    SALDO_INICIAL = 100_000.00  # Saldo inicial en dólares definido en la lógica de negocio

    def __init__(self) -> None: # Ejecución automática al iniciar sesión
        self.saldo      = self.SALDO_INICIAL # Asignación de los 100.000$
        self.portafolio = crear_portafolio() # Asignación de un nuevo diccionario vacío (función de portafolio.py)
        self.historial: list[dict] = [] # Asignación de una lista vacía que guardará las operaciones (IMPORTANTE EN LA ÚLTIMA FUNCIÓN)

    # ─────────────────────────────────────────────────────────
    # FUNCIÓN DE COMPRA
    # ─────────────────────────────────────────────────────────

    def comprar(
        self, simbolo: str, cantidad: int, precio_actual: float, timestamp_precio: float
    ) -> tuple[bool, str]:
        """
        A partir de la orden del FrontEnd de intentar ejecutar una compra, devuelve (éxito, mensaje).
        Recibe el Ticker, la cantidad, su precio actual y la hora a la que se adquirió el precio.
        """
        exito, mensaje, nuevo_saldo, precio_compra = validar_transaccion_compra(
            self.saldo, precio_actual, cantidad, timestamp_precio
        ) # Validación de la compra con la función de cálculos.py

        if exito: # Compra exitosa
            self.saldo      = nuevo_saldo # Actualización de saldo
            self.portafolio = registrar_compra(self.portafolio, simbolo, cantidad, precio_compra) # Registro de la compra en el portafolio: añade las acciones (Función de portafolio.py)
            self._registrar_operacion("COMPRA", simbolo, cantidad, precio_compra) # Registro de la compra en el historial de operaciones

        return exito, mensaje # Devuelve al dashboard el éxito o fracaso de la compra

    # ─────────────────────────────────────────────────────────
    # FUNCIÓN VENTA
    # ─────────────────────────────────────────────────────────

    def vender(
        self, simbolo: str, cantidad: int, precio_actual: float, timestamp_precio: float
    ) -> tuple[bool, str]:
        """
        A partir de la orden del FrontEnd de intentar ejecutar una venta, devuelve (éxito, mensaje).
        Recibe el Ticker, la cantidad, su precio actual y la hora a la que se adquirió el precio.
        """
        exito, mensaje, monto_recibido = validar_transaccion_venta(
            self.portafolio, simbolo, cantidad, precio_actual, timestamp_precio
        ) # Validación de la venta con la función de cálculos.py

        if exito: # Venta exitosa
            self.saldo     += monto_recibido # Se añade lo recibido al saldo
            self.portafolio = registrar_venta(self.portafolio, simbolo, cantidad) # Registro de la venta en el portafolio: retira las acciones (Función de portafolio.py)
            self._registrar_operacion("VENTA", simbolo, cantidad, precio_actual) # Registro de la venta en el historial de operaciones

        return exito, mensaje # Devuelve al dashboard el éxito o fracaso de la venta

    # ─────────────────────────────────────────────────────────
    # FUNCIÓN DE RESUMEN
    # ─────────────────────────────────────────────────────────

    def get_resumen(self, precios_actuales: dict) -> dict:
        """
        Función que utiliza el estado completo de la sesión para elaborar el dashboard.
        Por cada acción del portafolio se crea un diccionario que incluye:
            simbolo, cantidad, precio_compra, precio_actual, rendimiento_%
        """
        posiciones = [ # List Comprehension: creación de listas mediante iteración sobre listas existentes
            {
                "simbolo"       : simbolo,
                "cantidad"      : datos["cantidad"],
                "precio_compra" : datos["precio_compra_promedio"],
                "precio_actual" : precios_actuales.get(simbolo),
                "rendimiento_%" : calcular_rendimiento(
                    datos["precio_compra_promedio"],
                    precios_actuales.get(simbolo, 0),
                ), # Cálculo del rendimiento de cada acción con la función de calculos.py
            }
            for simbolo, datos in self.portafolio.items() # Recorre el inventario de acciones
        ]

        valor_portafolio = calcular_valor_portafolio(self.portafolio, precios_actuales) # Suma del valor de todas las acciones (función de portafolio.py)

        return { # Diccionario que se envia al Dashboard
            "saldo_disponible"  : round(self.saldo, 2),
            "valor_portafolio"  : valor_portafolio,
            "patrimonio_total"  : round(self.saldo + valor_portafolio, 2), # Suma del saldo con el valor del portafolio
            "posiciones"        : posiciones,
            "total_operaciones" : len(self.historial), # Longitud del historial de operaciones
        }

    # ─────────────────────────────────────────────────────────
    # FUNCIÓN DE REGISTRO EN EL HISTORIAL (interna, el Dashboard no la llama)
    # ─────────────────────────────────────────────────────────

    def _registrar_operacion(self, tipo: str, simbolo: str, cantidad: int, precio: float) -> None:
        """Agrega una operación al historial en memoria. Uso interno."""
        self.historial.append({ # Agrega a la lista vacía del inicio todos los datos de la nueva transacción
            "tipo"     : tipo,
            "simbolo"  : simbolo,
            "cantidad" : cantidad,
            "precio"   : precio,
            "hora"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
