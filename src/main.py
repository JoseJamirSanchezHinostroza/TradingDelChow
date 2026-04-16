# 1. IMPORTACIÓN: Aquí es donde conectamos las carpetas
from backend import conexion_api  # Trabajo del Encargado BackEnd
from logic import reglas_negocio   # Trabajo del Encargado Logic
from frontend import interfaz      # Trabajo del Encargado FrontEnd

def iniciar_programa():
    print("--- Bienvenido a TradeaYa! ---")
    
    # FLUJO LOGICO:
    # 1. El backend trae el precio
    precio = backend.conexion_api.obtener_precio_real("AAPL")
    
    # 2. Tu lógica calcula si se puede comprar
    resultado = logic.reglas_negocio.validar_compra(precio, cantidad=10, saldo=10000)
    
    # 3. El frontend muestra el resultado al usuario
    frontend.interfaz.mostrar_mensaje(resultado)

if __name__ == "__main__":
    iniciar_programa()
