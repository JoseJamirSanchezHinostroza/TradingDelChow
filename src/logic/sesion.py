"""
logic/sesion.py - TradeaYa!
Fachada que une calculos.py y portafolio.py en un único objeto.
El frontend solo necesita hablar con SesionTrading.
"""

from datetime import datetime

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
    Representa la sesión activa de un usuario.

    Mantiene en memoria:
        • saldo       – dinero disponible para operar
        • portafolio  – acciones actuales con precio promedio
        • historial   – lista de operaciones realizadas en esta sesión
    """

    SALDO_INICIAL = 100_000.00  # Dólares ficticios de arranque

    def __init__(self) -> None:
        self.saldo      = self.SALDO_INICIAL
        self.portafolio = crear_portafolio()
        self.historial: list[dict] = []

    # ─────────────────────────────────────────────────────────
    # COMPRA
    # ─────────────────────────────────────────────────────────

    def comprar(
        self, simbolo: str, cantidad: int, precio_actual: float, timestamp_precio: float
    ) -> tuple[bool, str]:
        """
        Intenta ejecutar una compra.
        Devuelve (éxito, mensaje).
        """
        exito, mensaje, nuevo_saldo, precio_compra = validar_transaccion_compra(
            self.saldo, precio_actual, cantidad, timestamp_precio
        )

        if exito:
            self.saldo      = nuevo_saldo
            self.portafolio = registrar_compra(self.portafolio, simbolo, cantidad, precio_compra)
            self._registrar_operacion("COMPRA", simbolo, cantidad, precio_compra)

        return exito, mensaje

    # ─────────────────────────────────────────────────────────
    # VENTA
    # ─────────────────────────────────────────────────────────

    def vender(
        self, simbolo: str, cantidad: int, precio_actual: float, timestamp_precio: float
    ) -> tuple[bool, str]:
        """
        Intenta ejecutar una venta.
        Devuelve (éxito, mensaje).
        """
        exito, mensaje, monto_recibido = validar_transaccion_venta(
            self.portafolio, simbolo, cantidad, precio_actual, timestamp_precio
        )

        if exito:
            self.saldo     += monto_recibido
            self.portafolio = registrar_venta(self.portafolio, simbolo, cantidad)
            self._registrar_operacion("VENTA", simbolo, cantidad, precio_actual)

        return exito, mensaje

    # ─────────────────────────────────────────────────────────
    # RESUMEN (para el dashboard)
    # ─────────────────────────────────────────────────────────

    def get_resumen(self, precios_actuales: dict) -> dict:
        """
        Estado completo de la sesión, listo para pintar el dashboard.

        Por cada posición incluye:
            simbolo, cantidad, precio_compra, precio_actual, rendimiento_%
        """
        posiciones = [
            {
                "simbolo"       : simbolo,
                "cantidad"      : datos["cantidad"],
                "precio_compra" : datos["precio_compra_promedio"],
                "precio_actual" : precios_actuales.get(simbolo),
                "rendimiento_%" : calcular_rendimiento(
                    datos["precio_compra_promedio"],
                    precios_actuales.get(simbolo, 0),
                ),
            }
            for simbolo, datos in self.portafolio.items()
        ]

        valor_portafolio = calcular_valor_portafolio(self.portafolio, precios_actuales)

        return {
            "saldo_disponible"  : round(self.saldo, 2),
            "valor_portafolio"  : valor_portafolio,
            "patrimonio_total"  : round(self.saldo + valor_portafolio, 2),
            "posiciones"        : posiciones,
            "total_operaciones" : len(self.historial),
        }

    # ─────────────────────────────────────────────────────────
    # HISTORIAL (interno)
    # ─────────────────────────────────────────────────────────

    def _registrar_operacion(self, tipo: str, simbolo: str, cantidad: int, precio: float) -> None:
        """Agrega una operación al historial en memoria. Uso interno."""
        self.historial.append({
            "tipo"     : tipo,
            "simbolo"  : simbolo,
            "cantidad" : cantidad,
            "precio"   : precio,
            "hora"     : datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })
