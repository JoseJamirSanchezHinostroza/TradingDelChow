"""
backend/main.py - TradeaYa!
Módulo de prueba manual del backend: login, consulta de precio y compra.
Ejecutar desde src/backend/ con: python main.py
"""

from database import DatabaseManager
from trade_engine import TradeEngine
from data_loader import DataLoader


def ejecutar_sistema() -> None:
    db     = DatabaseManager()
    motor  = TradeEngine()
    loader = DataLoader()

    print("=== TRADEAYA: MÓDULO DE PRUEBAS BACKEND ===\n")

    # Registrar usuario de prueba (ignorar si ya existe)
    db.registrar_usuario("Estudiante UNMSM", "software@unmsm.edu.pe", "1234")

    # Login
    email    = input("Email (software@unmsm.edu.pe): ").strip()
    password = input("Contraseña (1234): ").strip()
    usuario  = db.verificar_login(email, password)

    if not usuario:
        print("❌ Credenciales incorrectas.")
        return

    u_id, nombre, saldo = usuario
    print(f"\n✅ Bienvenido, {nombre}. Saldo: ${saldo:,.2f}")

    # Consulta y compra
    ticker = input("\n¿Qué acción deseas consultar? (ej: AAPL, MSFT): ").strip().upper()
    precio = motor.obtener_precio_actual(ticker)

    if not precio:
        print("❌ No se pudo obtener el precio. Verifica el ticker o tu conexión.")
        return

    print(f"📈 Precio actual de {ticker}: ${precio:,.2f}")
    cantidad   = int(input(f"¿Cuántas acciones de {ticker} deseas comprar?: "))
    costo_total = precio * cantidad

    if saldo < costo_total:
        print(f"❌ Saldo insuficiente. Necesitas ${costo_total:,.2f}, tienes ${saldo:,.2f}.")
        return

    nuevo_saldo = saldo - costo_total
    if db.guardar_compra(u_id, ticker, cantidad, precio, nuevo_saldo):
        print(f"🚀 Compra exitosa. Nuevo saldo: ${nuevo_saldo:,.2f}")
        print(loader.exportar_historial_usuario(u_id))
    else:
        print("❌ Error al guardar en la base de datos.")


if __name__ == "__main__":
    ejecutar_sistema()
