"""
backend/trade_engine.py - TradeaYa!
Puente con APIs externas: Alpaca (órdenes reales) y yfinance (precios).
La lógica de validación vive en logic/calculos.py, no aquí.
"""

from __future__ import annotations   # Permite usar tipos como "float | None" en versiones de Python anteriores a 3.10

import os                            # Módulo estándar para interactuar con el sistema operativo; se usa aquí para leer variables de entorno

import yfinance as yf                # Librería que consume la API de Yahoo Finance para obtener precios y datos históricos de acciones
from dotenv import load_dotenv       # Función que carga las variables de un archivo .env al entorno del proceso actual

load_dotenv()                        # Lee el archivo .env del directorio actual y establece sus pares clave=valor como variables de entorno (ALPACA_KEY, ALPACA_SECRET, etc.)


class TradeEngine:
    """Gestiona precios vía yfinance y órdenes opcionales vía Alpaca."""

    def __init__(self) -> None:          # Constructor: se ejecuta al crear una instancia de TradeEngine
        self._api = self._conectar_alpaca()  # Intenta conectar con Alpaca y guarda el cliente como atributo privado; será None si la conexión falla

    # ─────────────────────────────────────────────────────────
    # CONEXIÓN ALPACA
    # ─────────────────────────────────────────────────────────

    def _conectar_alpaca(self):          # Método privado (guión bajo al inicio); solo lo usa __init__ internamente
        """Inicializa el cliente de Alpaca. Devuelve None si las credenciales faltan."""
        key      = os.getenv("ALPACA_KEY")       # Lee la clave pública de la API de Alpaca desde las variables de entorno cargadas por load_dotenv()
        secret   = os.getenv("ALPACA_SECRET")    # Lee la clave secreta de Alpaca desde las variables de entorno
        endpoint = os.getenv("ALPACA_ENDPOINT")  # Lee la URL del endpoint de Alpaca (paper trading o producción) desde las variables de entorno

        if not all([key, secret, endpoint]):     # Verifica que los tres valores existan y no sean None ni cadena vacía; all() devuelve False si alguno falta
            print("⚠️  Credenciales de Alpaca no configuradas. Modo solo-precios activo.")  # Avisa que la app funcionará sin Alpaca (solo consulta de precios)
            return None                          # Devuelve None; self._api será None y los métodos que lo usan verificarán esto antes de ejecutar

        try:                                     # Intenta importar e instanciar el cliente de Alpaca; puede fallar si la librería no está instalada
            import alpaca_trade_api as tradeapi  # Importación diferida: solo se ejecuta si las credenciales están presentes, evitando error si no está instalada
            return tradeapi.REST(key, secret, endpoint, api_version="v2")  # Crea y devuelve el cliente REST de Alpaca autenticado con las credenciales cargadas
        except ImportError:                      # Captura el error específico que ocurre cuando la librería "alpaca-trade-api" no está instalada en el entorno
            print("⚠️  alpaca-trade-api no instalado. Modo solo-precios activo.")  # Avisa que el paquete falta; la app seguirá funcionando sin él
            return None                          # Devuelve None para indicar que Alpaca no está disponible

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
            hist = yf.Ticker(ticker).history(period=periodo)  # Descarga el historial OHLCV del ticker para el período indicado (ej: "1mo", "3mo", "1y") como DataFrame
            if hist.empty:                                     # Verifica si el DataFrame está vacío; ocurre con tickers inválidos o fuera de mercado
                return None                                    # Devuelve None para indicar que no hay datos disponibles
            return hist["Close"].to_dict()                     # Extrae solo la columna de precios de cierre y la convierte a diccionario {Timestamp: precio}
        except Exception as e:                                 # Captura cualquier error durante la descarga o procesamiento
            print(f"❌ Error al cargar historial de {ticker}: {e}")  # Imprime el error en consola para diagnóstico, incluyendo el ticker afectado
            return None                                        # Devuelve None para indicar fallo al llamador

    def validar_ticker(self, ticker: str) -> bool:             # Recibe un símbolo bursátil y devuelve True si existe en yfinance, False si no
        """True si el ticker existe en yfinance."""
        try:
            return bool(yf.Ticker(ticker).info)                # Descarga el diccionario de info del ticker; si está vacío o no existe, bool() lo convierte a False
        except Exception:                                      # Captura errores de red o tickers completamente inválidos
            return False                                       # Devuelve False indicando que el ticker no es válido o no pudo verificarse

    # ─────────────────────────────────────────────────────────
    # CUENTA ALPACA
    # ─────────────────────────────────────────────────────────

    def obtener_saldo_alpaca(self) -> float | str:             # Devuelve el saldo como float si Alpaca está conectado, o un string de error/aviso si no
        """Saldo de la cuenta Alpaca (paper trading). Solo informativo."""
        if self._api is None:                                  # Verifica si Alpaca no está conectado (self._api es None cuando las credenciales faltan o el paquete no está)
            return "Alpaca no conectado."                      # Devuelve un mensaje informativo en lugar de un número
        try:
            return float(self._api.get_account().cash)         # Consulta la cuenta Alpaca, extrae el campo "cash" (efectivo disponible) y lo convierte a float
        except Exception as e:                                 # Captura errores de red o de autenticación con Alpaca
            return f"❌ Error Alpaca: {e}"                     # Devuelve el mensaje de error como string para que la UI pueda mostrarlo

    # ─────────────────────────────────────────────────────────
    # ÓRDENES ALPACA
    # ─────────────────────────────────────────────────────────

    def enviar_orden_compra(self, ticker: str, cantidad: int) -> str:  # Recibe ticker y cantidad; devuelve un mensaje de éxito o error como string
        """
        Envía una orden de compra a mercado a Alpaca.
        Las validaciones de saldo y horario se hacen en logic/calculos.py.
        """
        if self._api is None:                                  # Verifica si Alpaca no está conectado antes de intentar enviar la orden
            return "❌ Alpaca no conectado."                   # Devuelve mensaje de error si no hay cliente disponible
        try:
            self._api.submit_order(
                symbol=ticker,                                 # Ticker de la acción a comprar (ej: "AAPL")
                qty=cantidad,                                  # Número de acciones a comprar
                side="buy",                                    # Dirección de la orden: "buy" para compra (alternativa sería "sell")
                type="market",                                 # Tipo de orden: "market" se ejecuta al precio actual del mercado sin límite de precio
                time_in_force="gtc",                           # "Good Till Cancelled": la orden permanece activa hasta ejecutarse o cancelarse manualmente
            )
            return f"✅ Orden de compra enviada: {cantidad} × {ticker}"  # Confirma que la orden fue enviada exitosamente a Alpaca
        except Exception as e:                                 # Captura errores de la API de Alpaca (fondos insuficientes, mercado cerrado, ticker inválido, etc.)
            return f"❌ Error al enviar orden: {e}"            # Devuelve el mensaje de error de Alpaca para que pueda mostrarse en la interfaz
