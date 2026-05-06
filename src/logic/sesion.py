"""
Módulo de Sesión - TradeaYa!
Une calculos.py y portafolio.py en un objeto único.
El frontend solo necesita hablar con este archivo.
"""

# ─────────────────────────────────────────────────────────
# SECCIÓN 1: Importar las funciones importantes
# ─────────────────────────────────────────────────────────
from calculos    import validar_transaccion_compra, validar_transaccion_venta, calcular_rendimiento
from portafolio  import (crear_portafolio, registrar_compra, registrar_venta,
                         obtener_posicion, calcular_valor_portafolio)


# ─────────────────────────────────────────────────────────
# SECCIÓN 2: Sesion de usuario
# ─────────────────────────────────────────────────────────
class SesionTrading:
    """
    Representa la sesión activa de un usuario en TradeaYa!

    Guarda en memoria:
        - El saldo disponible
        - El portafolio actual
        - El historial de operaciones

    El frontend crea UNA instancia al inicio y la usa durante toda la sesión.
    """

    SALDO_INICIAL = 100_000.00  # $100,000 dólares ficticios para empezar

    def __init__(self):
        self.saldo      = self.SALDO_INICIAL
        self.portafolio = crear_portafolio()
        self.historial  = []               # Lista de operaciones realizadas

    # ─────────────────────────────────────────
    # COMPRA
    # ─────────────────────────────────────────

    def comprar(self, simbolo, cantidad_a_comprar, precio_actual, timestamp_precio):
        """
        Intenta ejecutar una compra.

        Devuelve:
            (bool, str)  →  (éxito, mensaje para mostrar al usuario)
        """
        exito, mensaje, nuevo_saldo, precio_compra = validar_transaccion_compra(
            self.saldo, precio_actual, cantidad_a_comprar, timestamp_precio
        )

        if exito:
            self.saldo      = nuevo_saldo
            self.portafolio = registrar_compra(self.portafolio, simbolo, cantidad_comprada, precio_compra)
            self._registrar_en_historial("COMPRA", simbolo, cantidad_a_comprar, precio_compra)

        return exito, mensaje

    # ─────────────────────────────────────────
    # VENTA
    # ─────────────────────────────────────────

    def vender(self, simbolo, cantidad_a_vender, precio_actual, timestamp_precio):
        """
        Intenta ejecutar una venta.

        Devuelve:
            (bool, str)  →  (éxito, mensaje para mostrar al usuario)
        """
        exito, mensaje, monto_recibido = validar_transaccion_venta(
            self.portafolio, simbolo, cantidad_a_vender, precio_actual, timestamp_precio
        )

        if exito:
            self.saldo     += monto_recibido
            self.portafolio = registrar_venta(self.portafolio, simbolo, cantidad_vendida)
            self._registrar_en_historial("VENTA", simbolo, cantidad_a_vender, precio_actual)

        return exito, mensaje

    # ─────────────────────────────────────────
    # CONSULTAS
    # ─────────────────────────────────────────

    def get_resumen(self, precios_actuales):
        """
        Devuelve un diccionario con el estado completo de la sesión.
        El frontend usa esto para pintar el dashboard.

        Incluye por cada acción:
            - Cantidad poseída
            - Precio de compra promedio
            - Precio actual
            - Rendimiento en %
        """
        posiciones = []

        for simbolo, datos in self.portafolio.items():
            precio_hoy = precios_actuales.get(simbolo)
            rendimiento = None

            if precio_hoy is not None:
                rendimiento = calcular_rendimiento(datos["precio_compra_promedio"], precio_hoy)

            posiciones.append({
                "simbolo"        : simbolo,
                "cantidad"       : datos["cantidad"],
                "precio_compra"  : datos["precio_compra_promedio"],
                "precio_actual"  : precio_hoy,
                "rendimiento_%"  : rendimiento
            })

        return {
            "saldo_disponible"    : round(self.saldo, 2),
            "valor_portafolio"    : calcular_valor_portafolio(self.portafolio, precios_actuales),
            "patrimonio_total"    : round(self.saldo + calcular_valor_portafolio(self.portafolio, precios_actuales), 2),
            "posiciones"          : posiciones,
            "total_operaciones"   : len(self.historial)
        }

    # ─────────────────────────────────────────
    # HISTORIAL (interno)
    # ─────────────────────────────────────────

    def _registrar_en_historial(self, tipo, simbolo, cantidad, precio):
        """
        Guarda cada operación ejecutada en la lista de historial.
        El guión bajo indica que es de uso interno (no lo llama el frontend).
        """
        from datetime import datetime
        self.historial.append({
            "tipo"     : tipo,
            "simbolo"  : simbolo,
            "cantidad" : cantidad,
            "precio"   : precio,
            "hora"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
