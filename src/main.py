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





main.py - Prueba de la lógica de TradeaYa! sin backend real
Simula precios y timestamps para verificar que todo funciona.
"""

import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src", "logic"))

from sesion import SesionTrading

# ── Simulación de datos que vendría del backend ──────────────
precios_falsos    = {"AAPL": 195.30, "TSLA": 185.50, "NVDA": 430.00}
timestamp_fresco  = time.time()          # Ahora mismo = precio válido
timestamp_viejo   = time.time() - 120   # Hace 2 minutos = precio inválido

# ── Crear sesión ─────────────────────────────────────────────
sesion = SesionTrading()
print(f"\n💰 Saldo inicial: ${sesion.saldo:,.2f}\n")

# ── TEST 1: Compra válida ─────────────────────────────────────
exito, msg = sesion.comprar("AAPL", 10, precios_falsos["AAPL"], timestamp_fresco)
print(f"[TEST 1 - Compra AAPL x10]  {'✅' if exito else '❌'}  {msg}")

# ── TEST 2: Compra con precio viejo ───────────────────────────
exito, msg = sesion.comprar("TSLA", 5, precios_falsos["TSLA"], timestamp_viejo)
print(f"[TEST 2 - Precio viejo]     {'✅' if exito else '❌'}  {msg}")

# ── TEST 3: Venta válida parcial ──────────────────────────────
exito, msg = sesion.vender("AAPL", 3, precios_falsos["AAPL"], timestamp_fresco)
print(f"[TEST 3 - Venta AAPL x3]   {'✅' if exito else '❌'}  {msg}")

# ── TEST 4: Venta de acción que no tienes ─────────────────────
exito, msg = sesion.vender("NVDA", 1, precios_falsos["NVDA"], timestamp_fresco)
print(f"[TEST 4 - Vender sin tener] {'✅' if exito else '❌'}  {msg}")

# ── TEST 5: Saldo insuficiente ────────────────────────────────
exito, msg = sesion.comprar("NVDA", 1000, precios_falsos["NVDA"], timestamp_fresco)
print(f"[TEST 5 - Saldo insuf.]     {'✅' if exito else '❌'}  {msg}")

# ── Resumen final ─────────────────────────────────────────────
resumen = sesion.get_resumen(precios_falsos)
print("\n" + "─"*45)
print(f"  Saldo disponible  : ${resumen['saldo_disponible']:>12,.2f}")
print(f"  Valor portafolio  : ${resumen['valor_portafolio']:>12,.2f}")
print(f"  Patrimonio total  : ${resumen['patrimonio_total']:>12,.2f}")
print(f"  Operaciones hechas: {resumen['total_operaciones']}")
print("─"*45)
print("\n  📊 Posiciones actuales:")
for p in resumen["posiciones"]:
    print(f"     {p['simbolo']:5}  |  {p['cantidad']} acciones  "
          f"|  compra ${p['precio_compra']:.2f}  "
          f"|  hoy ${p['precio_actual']:.2f}  "
          f"|  {p['rendimiento_%']:+.2f}%")
