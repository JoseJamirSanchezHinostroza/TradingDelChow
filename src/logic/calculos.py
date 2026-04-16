"""
Módulo de Lógica de Negocio - TradeaYa!
Este archivo contiene los algoritmos de decisión y cálculos matemáticos.
"""
#.Validación de Saldo: El sistema no permitirá compras si el costo total de la transacción (precio de acción x cantidad) más la comisión excede el saldo disponible en la cuenta ficticia.
#.Gestión de Comisiones: Se aplicará una comisión fija o porcentual por cada operación realizada (ej. 0.5% por transacción) para simular los costos operativos de un broker real.
#.Horario de Mercado: Las operaciones de compra/venta solo se procesarán si el mercado de EE. UU. está abierto (Lunes a Viernes, 9:30 AM - 4:00 PM EST). Fuera de este horario, el sistema solo permitirá visualización.
#.Propiedad de Activos: El usuario solo podrá vender acciones que existan previamente en su portafolio y en cantidades iguales o menores a las que posee.
#.Actualización de Precios: Los precios de mercado deben refrescarse con una latencia máxima definida (ej. cada 15-60 segundos) para asegurar que la toma de decisiones se base en datos recientes.
"Comisión 0.5% del broker"
def calcular_comision(monto_total):  
    return monto_total * 0.005

"Calcula el costo de las acciones más la comisión del broker."
def calcular_monto_a_pagar(precio_actual, cantidad):
    monto_total = precio_actual * cantidad #Total sin incluir comisión
    comision = calcular_comision(monto_total)
    return monto_total + comision

"Validación de saldo suficiente"
def validar_transaccion(saldo_actual, precio_actual, cantidad): 
    monto_a_pagar = calcular_monto_a_pagar(precio_actual, cantidad)
    if saldo_actual >= monto_a_pagar: #Si nos alcanza...
        nuevo_saldo = saldo_actual - monto_a_pagar #Saldo que queda después de realizar la compra
        precio_compra = precio_actual #El precio actual del momento en que compramos pasa a ser el precio al que compramos
        return True, f"Compra exitosa. Nuevo saldo: ${nuevo_saldo:.2f}", nuevo_saldo
    else: #Si nos falta...
        falta = monto_a_pagar - saldo_actual #Saldo que nos faltó
        return False,f"Saldo insuficiente. Te faltan ${falta:.2f}", saldo_actual #Saldo se mantiene igual

"Calcula el porcentaje de ganancia o pérdida de una inversión."
def calcular_rendimiento(precio_compra, precio_actual): 
    rendimiento = ((precio_actual - precio_compra) / precio_compra) * 100
    return round(rendimiento, 2)
