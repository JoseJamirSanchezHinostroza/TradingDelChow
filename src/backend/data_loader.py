"""
backend/data_loader.py - TradeaYa!
Exportación de historial de usuario a CSV o JSON.
Los precios y gráficos ahora viven en TradeEngine para centralizar yfinance.
"""

import pandas as pd
from database import DatabaseManager


class DataLoader:
    """Genera reportes exportables del historial de transacciones."""

    def __init__(self) -> None:
        self.db = DatabaseManager()

    def exportar_historial_usuario(self, usuario_id: int, formato: str = "csv") -> str:
        """
        Exporta el historial de transacciones a un archivo CSV o JSON.
        Devuelve un mensaje de éxito o error.
        """
        try:
            with self.db.conectar() as conn:
                df = pd.read_sql_query(
                    "SELECT * FROM transacciones WHERE usuario_id = ?",
                    conn,
                    params=(usuario_id,),
                )

            nombre_archivo = f"historial_user_{usuario_id}.{formato}"

            if formato == "csv":
                df.to_csv(nombre_archivo, index=False)
            else:
                df.to_json(nombre_archivo, orient="records")

            return f"✅ Reporte generado: {nombre_archivo}"
        except Exception as e:
            return f"❌ Error al exportar: {e}"
