import yfinance as yf
import pandas as pd
from database import DatabaseManager

class DataLoader:
    def __init__(self):
        self.db = DatabaseManager()

    def obtener_datos_grafico(self, ticker, periodo="1mo"):
        """
        Para realizar los gráficos.
        """

        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period=period)
            if hist.empty:
                return None
            # Devolvemos solo lo necesario: Fecha y Precio de Cierre
            return hist['Close'].to_dict()
        except Exception as e:
            print(f"Error al cargar datos de mercado: {e}")
            return None

    def exportar_historial_usuario(self, usuario_id, formato="csv"):
        """
        Guarda el historial de transacciones en un archivo.
        """
        try:
            with self.db.conectar() as conn:
                query = "SELECT * FROM transacciones WHERE usuario_id = ?"
                df = pd.read_sql_query(query, conn, params=(usuario_id,))
            
            nombre_archivo = f"historial_user_{usuario_id}.{formato}"
            
            if formato == "csv":
                df.to_csv(nombre_archivo, index=False)
            else:
                df.to_json(nombre_archivo, orient="records")
                
            return f"✅ Reporte generado: {nombre_archivo}"
        except Exception as e:
            return f"❌ Error al exportar: {e}"
