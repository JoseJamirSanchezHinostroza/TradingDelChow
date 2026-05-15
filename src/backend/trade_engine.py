"""
backend/trade_engine.py - TradeaYa!
Puente con APIs externas: Alpaca (órdenes reales) y yfinance (precios).
La lógica de validación vive en logic/calculos.py, no aquí.
"""

from __future__ import annotations

import os

import yfinance as yf
from dotenv import load_dotenv

load_dotenv()


class TradeEngine:
    """Gestiona precios vía yfinance y órdenes opcionales vía Alpaca."""

    def __init__(self) -> None:
        self._api = self._conectar_alpaca()

    # ─────────────────────────────────────────────────────────
    # CONEXIÓN ALPACA
    # ─────────────────────────────────────────────────────────

    def _conectar_alpaca(self):
        """Inicializa el cliente de Alpaca. Devuelve None si las credenciales faltan."""
        key      = os.getenv("ALPACA_KEY")
        secret   = os.getenv("ALPACA_SECRET")
        endpoint = os.getenv("ALPACA_ENDPOINT")

        if not all([key, secret, endpoint]):
            print("⚠️  Credenciales de Alpaca no configuradas. Modo solo-precios activo.")
            return None

        try:
            import alpaca_trade_api as tradeapi
            return tradeapi.REST(key, secret, endpoint, api_version="v2")
        except ImportError:
            print("⚠️  alpaca-trade-api no instalado. Modo solo-precios activo.")
            return None

    # ─────────────────────────────────────────────────────────
    # PRECIOS (yfinance)
    # ─────────────────────────────────────────────────────────

    def obtener_precio_actual(self, ticker: str) -> float | None:
        """
        Precio de mercado más reciente del ticker.
        Devuelve None si el símbolo no existe o hay error de red.
        """
        try:
            return round(yf.Ticker(ticker).fast_info["last_price"], 2)
        except Exception:
            return None

    def obtener_datos_grafico(self, ticker: str, periodo: str = "1mo") -> dict | None:
        """
        Historial de precios de cierre para graficar.
        Devuelve { fecha: precio } o None si hay error.
        """
        try:
            hist = yf.Ticker(ticker).history(period=periodo)
            if hist.empty:
                return None
            return hist["Close"].to_dict()
        except Exception as e:
            print(f"❌ Error al cargar historial de {ticker}: {e}")
            return None

    def validar_ticker(self, ticker: str) -> bool:
        """True si el ticker existe en yfinance."""
        try:
            return bool(yf.Ticker(ticker).info)
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────
    # CUENTA ALPACA
    # ─────────────────────────────────────────────────────────

    def obtener_saldo_alpaca(self) -> float | str:
        """Saldo de la cuenta Alpaca (paper trading). Solo informativo."""
        if self._api is None:
            return "Alpaca no conectado."
        try:
            return float(self._api.get_account().cash)
        except Exception as e:
            return f"❌ Error Alpaca: {e}"

    # ─────────────────────────────────────────────────────────
    # ÓRDENES ALPACA
    # ─────────────────────────────────────────────────────────

    def enviar_orden_compra(self, ticker: str, cantidad: int) -> str:
        """
        Envía una orden de compra a mercado a Alpaca.
        Las validaciones de saldo y horario se hacen en logic/calculos.py.
        """
        if self._api is None:
            return "❌ Alpaca no conectado."
        try:
            self._api.submit_order(
                symbol=ticker,
                qty=cantidad,
                side="buy",
                type="market",
                time_in_force="gtc",
            )
            return f"✅ Orden de compra enviada: {cantidad} × {ticker}"
        except Exception as e:
            return f"❌ Error al enviar orden: {e}"
