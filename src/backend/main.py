"""
backend/main.py - TradeaYa!
Módulo de prueba manual del backend: login, consulta de precio y compra.
Ejecutar desde src/backend/ con: python main.py
"""

from database import DatabaseManager   # Importa la clase que gestiona todas las operaciones con la base de datos SQLite
from trade_engine import TradeEngine   # Importa la clase que conecta con yfinance (precios) y Alpaca (órdenes)
from data_loader import DataLoader     # Importa la clase que genera reportes exportables del historial


def ejecutar_sistema() -> None:        # Define la función principal del script; -> None indica que no retorna ningún valor
    db     = DatabaseManager()         # Crea una instancia del gestor de base de datos (también crea las tablas si no existen)
    motor  = TradeEngine()             # Crea una instancia del motor de trading (intenta conectarse a Alpaca al inicializarse)
    loader = DataLoader()              # Crea una instancia del generador de reportes

    print("=== TRADEAYA: MÓDULO DE PRUEBAS BACKEND ===\n")  # Imprime un encabezado decorativo en la consola

    # Registrar usuario de prueba (ignorar si ya existe)
    db.registrar_usuario("Estudiante UNMSM", "software@unmsm.edu.pe", "1234")  # Intenta crear el usuario de prueba; si ya existe, la DB lo ignora automáticamente

    # Login
    email    = input("Email (software@unmsm.edu.pe): ").strip()    # Solicita el email al usuario por consola y elimina espacios en blanco al inicio/final
    password = input("Contraseña (1234): ").strip()                 # Solicita la contraseña por consola y elimina espacios en blanco al inicio/final
    usuario  = db.verificar_login(email, password)                  # Consulta la DB: devuelve (id, nombre, saldo) si las credenciales son válidas, o None si no

    if not usuario:                                                  # Evalúa si el login falló (usuario es None)
        print("❌ Credenciales incorrectas.")                        # Informa al usuario que las credenciales son incorrectas
        return                                                       # Detiene la ejecución de la función inmediatamente

    u_id, nombre, saldo = usuario                                    # Desempaqueta la tupla devuelta por verificar_login en tres variables separadas
    print(f"\n✅ Bienvenido, {nombre}. Saldo: ${saldo:,.2f}")        # Saluda al usuario mostrando su saldo con formato de miles y 2 decimales

    # Consulta y compra
    ticker = input("\n¿Qué acción deseas consultar? (ej: AAPL, MSFT): ").strip().upper()  # Solicita el símbolo bursátil, elimina espacios y lo convierte a mayúsculas
    precio = motor.obtener_precio_actual(ticker)                                           # Consulta el precio actual del ticker en yfinance; devuelve float o None si falla

    if not precio:                                                                         # Evalúa si no se pudo obtener el precio (precio es None o 0)
        print("❌ No se pudo obtener el precio. Verifica el ticker o tu conexión.")        # Informa el problema al usuario
        return                                                                             # Detiene la ejecución de la función

    print(f"📈 Precio actual de {ticker}: ${precio:,.2f}")                                # Muestra el precio actual con formato de miles y 2 decimales
    cantidad    = int(input(f"¿Cuántas acciones de {ticker} deseas comprar?: "))          # Solicita la cantidad a comprar y la convierte a entero
    costo_total = precio * cantidad                                                        # Calcula el costo total multiplicando precio unitario por cantidad

    if saldo < costo_total:                                                                # Verifica si el saldo del usuario es insuficiente para la compra
        print(f"❌ Saldo insuficiente. Necesitas ${costo_total:,.2f}, tienes ${saldo:,.2f}.")  # Informa el déficit mostrando cuánto se necesita vs. cuánto hay
        return                                                                             # Detiene la ejecución de la función

    nuevo_saldo = saldo - costo_total                                                      # Calcula el saldo resultante restando el costo total al saldo actual
    if db.guardar_compra(u_id, ticker, cantidad, precio, nuevo_saldo):                     # Intenta guardar la compra en la DB (actualiza saldo, transacciones y portafolio)
        print(f"🚀 Compra exitosa. Nuevo saldo: ${nuevo_saldo:,.2f}")                      # Confirma la compra mostrando el nuevo saldo
        print(loader.exportar_historial_usuario(u_id))                                     # Exporta y muestra el historial de transacciones del usuario
    else:                                                                                   # Si guardar_compra devolvió False, algo falló en la DB
        print("❌ Error al guardar en la base de datos.")                                   # Informa el error al usuario


if __name__ == "__main__":   # Comprueba que este archivo se está ejecutando directamente (no siendo importado por otro módulo)
    ejecutar_sistema()       # Llama a la función principal para iniciar el flujo del script

