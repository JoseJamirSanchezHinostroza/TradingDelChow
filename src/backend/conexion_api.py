import alpaca_trade_api as tradeapi
import os
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

class TradeEngine:
    def __init__(self):
        # Configuramos la conexión interna
        self.key = os.getenv('ALPACA_KEY')
        self.secret = os.getenv('ALPACA_SECRET')
        self.endpoint = os.getenv('ALPACA_ENDPOINT')
        self.api = tradeapi.REST(self.key, self.secret, self.endpoint, api_version='v2')

    def obtener_saldo(self):
        """Devuelve el dinero disponible en la cuenta."""
        try:
            account = self.api.get_account()
            return float(account.cash)
        except Exception as e:
            return f"Error: {e}"

    def obtener_precio_actual(self, simbolo):
        """Busca el precio de una acción (ej: 'AAPL' para Apple)."""
        try:
            # Usamos yfinance para datos rápidos de mercado
            ticker = yf.Ticker(simbolo)
            precio = ticker.history(period='1d')['Close'].iloc[-1]
            return round(precio, 2)
        except Exception:
            return "No se encontró el símbolo"

    def comprar_accion(self, simbolo, cantidad):
        """Ejecuta una orden de compra real en el simulador."""
        try:
            self.api.submit_order(
                symbol=simbolo,
                qty=cantidad,
                side='buy',
                type='market',
                time_in_force='gtc'
            )
            return f"Compra exitosa de {cantidad} acciones de {simbolo}"
        except Exception as e:
            return f"Error en la compra: {e}"
        
        # --- ESTO VA AL FINAL DEL ARCHIVO ---
if __name__ == "__main__":
    # Creamos el objeto del motor
    motor = TradeEngine()
    
    # Probamos la conexión obteniendo el saldo
    saldo = motor.obtener_saldo()
    print(f"✅ ¡Conexión exitosa! Saldo actual: ${saldo}")
    
    # Probamos buscando el precio de una acción
    precio_apple = motor.obtener_precio_actual('AAPL')
    print(f"📈 Precio actual de Apple (AAPL): ${precio_apple}")
