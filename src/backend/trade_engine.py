import yfinance as yf
import time

class TradeEngine:
    def obtener_precio_actual(self, ticker):
        """Obtiene el precio real. Si falla, devuelve None para manejarlo en el main."""
        try:
            stock = yf.Ticker(ticker)
            precio = stock.fast_info['last_price']
            return round(precio, 2)
        except:
            return None

    def validar_ticker(self, ticker):
        """Verifica si el símbolo existe para que se pueda mostrar un error en el buscador."""
        try:
            stock = yf.Ticker(ticker)
            return stock.info is not None
        except:
            return False
