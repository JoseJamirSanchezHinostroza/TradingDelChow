import alpaca_trade_api as tradeapi
import os
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

class TradeEngine:
    def __init__(self):
        # Conectamos con Alpaca usando las variables del.env
        self.key = os.getenv('ALPACA_KEY')
        self.secret = os.getenv('ALPACA_SECRET')
        self.endpoint = os.getenv('ALPACA_ENDPOINT')
        
        # Esto permite que, en el futuro, se pueda ejecutar órdenes reales si se desea
        try:
            self.api = tradeapi.REST(self.key, self.secret, self.endpoint, api_version='v2')
        except Exception as e:
            print(f"Advertencia: No se pudo conectar con Alpaca: {e}")

    def obtener_precio_actual(self, simbolo):
        """Busca el precio real. Es la base para calcular cuánto descontar del saldo."""
        try:
            # Usa fast_info porque es más rápido que history para precios únicos
            ticker = yf.Ticker(simbolo)
            precio = ticker.fast_info['last_price']
            
            if precio is None or precio <= 0:
                return None
                
            return round(precio, 2)
        except Exception:
            return None

    def validar_ticker(self, simbolo):
        """Verifica si la acción existe antes de intentar una compra."""
        precio = self.obtener_precio_actual(simbolo)
        return precio is not None
