"""
backend/trade_engine.py - TradeaYa!
Puente con Yahoo Finance (precios).
"""

from __future__ import annotations   # Permite usar tipos como "float | None" en versiones de Python anteriores a 3.10
import yfinance as yf                # Librería que consume la API de Yahoo Finance para obtener precios y datos históricos de acciones
import pandas as pd                      # Librería para manipulación de datos; se usa aquí para manejar los DataFrames que devuelve yfinance


class TradeEngine:
    """Gestiona precios vía yfinance y órdenes opcionales vía Alpaca."""

    # ─────────────────────────────────────────────────────────
    # PRECIOS (yfinance)
    # ─────────────────────────────────────────────────────────

    def obtener_precio_actual(self, ticker: str) -> float | None:   # Recibe un ticker y devuelve su precio como float, o None si hay error
        """
        Precio de mercado más reciente del ticker.
        Devuelve None si el símbolo no existe o hay error de red.
        """
        try:
            return round(yf.Ticker(ticker).fast_info["last_price"], 2)  # Crea un objeto Ticker, accede a fast_info (caché ligero sin descarga completa) y redondea el precio a 2 decimales
        except Exception:                        # Captura cualquier error: ticker inválido, sin conexión, campo ausente, etc.
            return None                          # Devuelve None para que el llamador pueda detectar el fallo sin que la app se rompa

    def obtener_datos_grafico(self, ticker: str, periodo: str = "1mo") -> dict | None:  # Recibe ticker y período (default 1 mes); devuelve dict de fechas:precios o None
        """
        Historial de precios de cierre para graficar.
        Devuelve { fecha: precio } o None si hay error.
        """
        try:
            if periodo == "1d":
               hist = yf.Ticker(ticker).history(period="1d", interval="5m") # Descarga datos de hoy con velas de 5 minutos 
            else:
               hist = yf.Ticker(ticker).history(period=periodo)  # Descarga el historial OHLCV del ticker para el período indicado (ej: "1mo", "3mo", "1y") como DataFrame
            
            if hist.empty:                                     # Verifica si el DataFrame está vacío; ocurre con tickers inválidos o fuera de mercado
                return None                                    # Devuelve None para indicar que no hay datos disponibles
            
            return hist                    # Extrae todo el DF OHLCV para el trazo de velas en mostrar gráfico
        
        except Exception as e:                                 # Captura cualquier error durante la descarga o procesamiento
            print(f"❌ Error al cargar historial de {ticker}: {e}")  # Imprime el error en consola para diagnóstico, incluyendo el ticker afectado
            return None                                        # Devuelve None para indicar fallo al llamador

    def validar_ticker(self, ticker: str) -> bool:             # Recibe un símbolo bursátil y devuelve True si existe en yfinance, False si no
        """True si el ticker existe en yfinance."""
        try:
            return bool(yf.Ticker(ticker).info)                # Descarga el diccionario de info del ticker; si está vacío o no existe, bool() lo convierte a False
        except Exception:                                      # Captura errores de red o tickers completamente inválidos
            return False                                       # Devuelve False indicando que el ticker no es válido o no pudo verificarse
