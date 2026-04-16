# Reglas de Negocio - TradeaYa!

def calcular_comision(monto_total):  """Comisión 0.5% del broker"""
    return monto_total * 0.005

def validar_compra(saldo_actual, precio_accion, cantidad): """Verifica si el usuario tiene dinero suficiente incluyendo comisión"""
    costo_acciones = precio_accion * cantidad
    comision = calcular_comision(costo_acciones)
    costo_total = costo_acciones + comision
    
    if saldo_actual >= costo_total:
        nuevo_saldo = saldo_actual - costo_total
        return True, nuevo_saldo
    else:
        return False, saldo_actual
