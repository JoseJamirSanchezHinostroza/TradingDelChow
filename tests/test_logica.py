"""
tests/test_logica.py - TradeaYa!
Prueba de la lógica de negocio sin backend real.
Simula precios y timestamps para verificar compra, venta y validaciones.

Ejecutar desde la raíz del proyecto con:
    python tests/test_logica.py
"""

import sys
import os
import time

# Agrega src/ al path para poder importar logic.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from logic.sesion import SesionTrading

# ── Datos de prueba ───────────────────────────────────────────────────────────
PRECIOS        = {"AAPL": 195.30, "TSLA": 185.50, "NVDA": 430.00}
TS_FRESCO      = time.time()        # Precio válido (ahora mismo)
TS_VENCIDO     = time.time() - 120  # Precio inválido (hace 2 minutos)

# ── Iniciar sesión ────────────────────────────────────────────────────────────
sesion = SesionTrading()
print(f"\n💰 Saldo inicial: ${sesion.saldo:,.2f}\n")


def caso(num: int, descripcion: str, exito: bool, msg: str) -> None:
    estado = "✅" if exito else "❌"
    print(f"[TEST {num}] {descripcion:<30} {estado}  {msg}")


# ── Tests ─────────────────────────────────────────────────────────────────────
exito, msg = sesion.comprar("AAPL", 10, PRECIOS["AAPL"], TS_FRESCO)
caso(1, "Compra AAPL ×10 (válida)",        exito, msg)

exito, msg = sesion.comprar("TSLA", 5, PRECIOS["TSLA"], TS_VENCIDO)
caso(2, "Compra con precio vencido",        not exito, msg)

exito, msg = sesion.vender("AAPL", 3, PRECIOS["AAPL"], TS_FRESCO)
caso(3, "Venta AAPL ×3 (parcial válida)",  exito, msg)

exito, msg = sesion.vender("NVDA", 1, PRECIOS["NVDA"], TS_FRESCO)
caso(4, "Vender acción no poseída",         not exito, msg)

exito, msg = sesion.comprar("NVDA", 1000, PRECIOS["NVDA"], TS_FRESCO)
caso(5, "Compra con saldo insuficiente",    not exito, msg)

# ── Resumen ───────────────────────────────────────────────────────────────────
resumen = sesion.get_resumen(PRECIOS)

print("\n" + "─" * 47)
print(f"  Saldo disponible  : ${resumen['saldo_disponible']:>12,.2f}")
print(f"  Valor portafolio  : ${resumen['valor_portafolio']:>12,.2f}")
print(f"  Patrimonio total  : ${resumen['patrimonio_total']:>12,.2f}")
print(f"  Operaciones hechas: {resumen['total_operaciones']}")
print("─" * 47)
print("\n  📊 Posiciones actuales:")

for p in resumen["posiciones"]:
    print(
        f"     {p['simbolo']:5}  |  {p['cantidad']} acc  "
        f"|  compra ${p['precio_compra']:.2f}  "
        f"|  hoy ${p['precio_actual']:.2f}  "
        f"|  {p['rendimiento_%']:+.2f}%"
    )
