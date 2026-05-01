import os
import sys
from conexion_api import TradeEngine

class TradeYaCLI:
    def __init__(self):
        self.engine = TradeEngine()
        self.usuario = "PeruDev"
        self.comision = 0.005  # 0.5%
        self.prompt = f"PS C:\\Users\\{self.usuario}\\TradeaYa> "

    def limpiar_pantalla(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def imprimir_bienvenida(self):
        print("TradeaYa! Shell [Versión 1.0.2026]")
        print("(c) PeruDevs Corporation. Todos los derechos reservados.\n")
        print("Comandos: saldo, precio <ticker>, comprar <ticker> <cant>, clear, exit\n")

    def ejecutar(self):
        self.limpiar_pantalla()
        self.imprimir_bienvenida()

        while True:
            # Captura la entrada del usuario simulando el prompt de PowerShell
            entrada = input(self.prompt).strip().lower().split()

            if not entrada:
                continue

            comando = entrada[0]

            if comando == "exit":
                print("Cerrando sesión en TradeaYa!...")
                break

            elif comando == "clear":
                self.limpiar_pantalla()
                self.imprimir_bienvenida()

            elif comando == "saldo":
                saldo = self.engine.obtener_saldo()
                print(f"Saldo disponible: ${saldo:,.2f}")

            elif comando == "precio":
                if len(entrada) < 2:
                    print("Error: Debe especificar un ticker. Uso: precio <ticker>")
                    continue
                ticker = entrada[1].upper()
                precio = self.engine.obtener_precio_actual(ticker)
                print(f"{ticker} -> ${precio}")

            elif comando == "comprar":
                if len(entrada) < 3:
                    print("Error: Uso: comprar <ticker> <cantidad>")
                    continue
                
                ticker = entrada[1].upper()
                try:
                    cantidad = int(entrada[2])
                    precio_u = self.engine.obtener_precio_actual(ticker)
                    
                    if isinstance(precio_u, str):
                        print(f"Error: {precio_u}")
                        continue

                    # Lógica de Algoritmos (Regla de Negocio)
                    costo_base = precio_u * cantidad
                    total_con_comision = costo_base * (1 + self.comision)
                    saldo_actual = self.engine.obtener_saldo()

                    if total_con_comision > saldo_actual:
                        print(f"Fondos insuficientes. Requerido: ${total_con_comision:.2f}")
                    else:
                        print(f"Ejecutando orden por ${total_con_comision:.2f}...")
                        res = self.engine.comprar_accion(ticker, cantidad)
                        print(res)

                except ValueError:
                    print("Error: La cantidad debe ser un número entero.")

            else:
                print(f"'{comando}' no se reconoce como un comando interno.")

if __name__ == "__main__":
    app = TradeYaCLI()
    app.ejecutar()

