"""
backend/data_loader.py - TradeaYa!
Exportación de historial de usuario a CSV o JSON.
Los precios y gráficos ahora viven en TradeEngine para centralizar yfinance.
"""

import pandas as pd              # Librería para manipulación de datos en tablas (DataFrames); permite leer SQL y exportar a CSV/JSON
from database import DatabaseManager  # Importa el gestor de base de datos para acceder al historial de transacciones


class DataLoader:
    """Genera reportes exportables del historial de transacciones."""

    def __init__(self) -> None:           # Constructor: se ejecuta automáticamente al crear una instancia de DataLoader
        self.db = DatabaseManager()       # Crea y guarda una instancia del gestor de DB; self.db estará disponible en todos los métodos de la clase

    def exportar_historial_usuario(self, usuario_id: int, formato: str = "csv") -> str:
        """
        Exporta el historial de transacciones a un archivo CSV o JSON.
        Devuelve un mensaje de éxito o error.
        """
        try:                                                           # Inicia un bloque de manejo de errores para capturar cualquier excepción
            with self.db.conectar() as conn:                           # Abre la conexión a la DB usando context manager (se cierra automáticamente al salir del bloque)
                df = pd.read_sql_query(                                # Ejecuta una consulta SQL y carga el resultado directamente en un DataFrame de pandas
                    "SELECT * FROM transacciones WHERE usuario_id = ?",  # Consulta SQL: selecciona todas las columnas de transacciones filtradas por usuario
                    conn,                                              # Pasa la conexión activa para que pandas sepa contra qué DB ejecutar la consulta
                    params=(usuario_id,),                              # Sustituye el "?" de la consulta por el ID del usuario (la coma crea una tupla de un elemento)
                )

            nombre_archivo = f"historial_user_{usuario_id}.{formato}"  # Construye el nombre del archivo usando el ID del usuario y la extensión elegida

            if formato == "csv":                                        # Evalúa si el formato solicitado es CSV
                df.to_csv(nombre_archivo, index=False)                  # Exporta el DataFrame a CSV; index=False evita escribir el índice numérico de pandas como columna
            else:                                                       # Si el formato no es "csv", se asume JSON
                df.to_json(nombre_archivo, orient="records")            # Exporta el DataFrame a JSON; orient="records" genera una lista de objetos [{col:val,...},...]

            return f"✅ Reporte generado: {nombre_archivo}"             # Devuelve un mensaje de éxito con el nombre del archivo generado
        except Exception as e:                                          # Captura cualquier excepción que haya ocurrido dentro del bloque try
            return f"❌ Error al exportar: {e}"                         # Devuelve un mensaje de error con la descripción de la excepción
