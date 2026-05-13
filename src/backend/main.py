from database import DatabaseManager
from trade_engine import TradeEngine
from data_loader import DataLoader
import time

def ejecutar_sistema():
    db = DatabaseManager()
    motor = TradeEngine()
    loader = DataLoader()

    print("=== SISTEMA TRADEAYA: MÓDULO DE PRUEBAS PARA BACKEND ===")
    
    # 1. Intentamos registrar al usuario de prueba
    # Usamos un bloque try por si ya existe, no se detenga el programa
    db.registrar_usuario("Estudiante UNMSM", "software@unmsm.edu.pe", "1234")
    
    # 2. Inicio de Sesión
    print("\n[LOGIN]")
    email = input("Introduce tu email (software@unmsm.edu.pe): ")
    password = input("Introduce tu contraseña (1234): ")
    
    usuario = db.verificar_login(email, password)
    
    if usuario:
        u_id, nombre, saldo = usuario
        print(f"\n✅ Acceso concedido. Bienvenido, {nombre}.")
        print(f"💰 Saldo inicial: ${saldo:,.2f}")
        
        # 3. Simulación de Compra
        print("\n[MERCADO EN TIEMPO REAL]")
        ticker = input("¿Qué acción deseas consultar? (ej: AAPL, MSFT, TSLA): ").upper()
        precio = motor.obtener_precio_actual(ticker)
        
        if precio:
            print(f"📈 El precio actual de {ticker} es: ${precio}")
            cantidad = int(input(f"¿Cuántas acciones de {ticker} deseas comprar?: "))
            costo_total = precio * cantidad
            
            if saldo >= costo_total:
                nuevo_saldo = saldo - costo_total
                # Guardamos en la base de datos
                if db.actualizar_saldo_y_compra(u_id, ticker, cantidad, precio, nuevo_saldo):
                    print(f"🚀 COMPRA EXITOSA. Nuevo saldo: ${nuevo_saldo:,.2f}")
                    
                    # 4. Exportar reporte
                    print("\n[REPORTES]")
                    print(loader.exportar_historial_usuario(u_id))
            else:
                print("❌ Saldo insuficiente para esta operación.")
        else:
            print("❌ No se pudo obtener el precio. Verifica el Ticker o tu conexión.")
    else:
        print("❌ Credenciales incorrectas.")

if __name__ == "__main__":
    ejecutar_sistema()
