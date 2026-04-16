# 1. IMPORTACIÓN: Aquí es donde conectamos las carpetas
from backend import conexion_api  # Lo que haga el Integrante 1
from logic import reglas_negocio   # LO QUE HACES TÚ (Integrante 3)
from frontend import interfaz      # Lo que haga el Integrante 2

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
