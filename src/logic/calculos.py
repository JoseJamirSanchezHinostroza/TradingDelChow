"""
Módulo de Lógica de Negocio - TradeaYa!
Se implementarán las siguientes reglas en el proyecto, de manera que puedan asegurar el correcto funcionamiento del mismo.
.Validación de Saldo: El sistema no permitirá compras si el costo total de la transacción (precio de acción x cantidad) más la comisión excede el saldo disponible en la cuenta ficticia.
.Gestión de Comisiones: Se aplicará una comisión fija o porcentual por cada operación realizada (0.5% por transacción) para simular los costos operativos de un broker real.
.Horario de Mercado: Las operaciones de compra/venta solo se procesarán si el mercado de EE. UU. está abierto (Lunes a Viernes, 9:30 AM - 4:00 PM EST). Fuera de este horario,
el sistema solo permitirá visualización. El sistema, sin embargo, podría permitir almacenar órdenes de compra para ejecutarlas tan pronto como el mercado vuelva a abrirse.
.Propiedad de Activos: El usuario solo podrá vender acciones que existan previamente en su portafolio y en cantidades iguales o menores a las que posee.
.Actualización de Precios: Los precios de mercado deben refrescarse con una latencia máxima definida (ej. cada 15-60 segundos) para asegurar que la toma de decisiones se base en datos recientes.
.Ejecución de Órdenes: El programa podría enseñar al usuario a ordenar la compra de acciones si es que el precio va debajo o sobre límites que se establecieron en la misma orden.
.Gestión de riesgo: Si la Ejecución de órdenes no está activada, cuando el precio cae por debajo de un cierto límite, el sistema vendería automáticamente para proteger capital y tiraría
una advertencia respecto a esto. En contrapunto, si sube por encima de un porcentaje, el sistema empezará a sugerir vender para obtener ganancias, y vendería automáticamente si empieza a
caer para asegurar ganancias.
"""
from datetime import datetime
import pytz # Librería para manejar zonas horarias
import time 

LATENCIA_MAXIMA_SEGUNDOS = 60 # Regla de negocio: 60 segundos máximo
COMISION_PORCENTAJE = 0.005  # 0.5%

"Verifica si el mercado de EE.UU. está abierto (Lunes-Viernes, 9:30 AM - 4:00 PM EST)."
def mercado_abierto():
    tz_ny = pytz.timezone('America/New_York') # Definimos la zona horaria de Nueva York
    ahora_ny = datetime.now(tz_ny)
    es_dia_semana = ahora_ny.weekday() < 5 # 1. Validar que sea día de semana (0=Lunes, 4=Viernes)
    hora_apertura = ahora_ny.replace(hour=9, minute=30, second=0, microsecond=0) # 2. Validar el rango de horas
    hora_cierre = ahora_ny.replace(hour=16, minute=0, second=0, microsecond=0)
    esta_en_horario = hora_apertura <= ahora_ny <= hora_cierre
    return es_dia_semana and esta_en_horario

"Comisión 0.5% del broker"
def calcular_comision(monto_total):  
    return monto_total * COMISION_PORCENTAJE

def es_precio_valido(timestamp_precio): # Verifica si el precio fue obtenido hace menos de 60 segundos.
#'timestamp_precio' es el momento en que el Backend trajo el dato.
    diferencia = time.time() - timestamp_precio
    return diferencia <= LATENCIA_MAXIMA_SEGUNDOS

"Calcula el costo de las acciones más la comisión del broker."
def calcular_monto_a_pagar(precio_actual, cantidad_a_comprar):
    monto_total = precio_actual * cantidad #Total sin incluir comisión
    comision = calcular_comision(monto_total)
    return monto_total + comision


"Validación de saldo suficiente, horario y frescura para comprar"
def validar_transaccion_compra(saldo_actual, precio_actual, cantidad_a_comprar, timestamp_precio):
    if not mercado_abierto():
        return False, "Mercado cerrado. Solo se permite visualización.", saldo_actual, None
    if not es_precio_valido(timestamp_precio):
        return False, "Precio desactualizado. Esperando actualización.", saldo_actual, None
    monto_a_pagar = calcular_monto_a_pagar(precio_actual, cantidad_a_comprar)
    if saldo_actual >= monto_a_pagar: #Si nos alcanza...
        nuevo_saldo = saldo_actual - monto_a_pagar #Saldo que queda después de realizar la compra
        precio_compra = precio_actual #El precio actual del momento en que compramos pasa a ser el precio al que compramos
        return True, f"Compra exitosa. Nuevo saldo: ${nuevo_saldo:.2f}", nuevo_saldo, precio_compra
    else: #Si nos falta...
        falta = monto_a_pagar - saldo_actual #Saldo que nos faltó
        return False,f"Saldo insuficiente. Te faltan ${falta:.2f}", saldo_actual, None #Saldo se mantiene igual

"Calcula la venta de las acciones restando la comisión del broker."
def calcular_monto_a_recibir(precio_actual, cantidad_a_vender):
    monto_total = precio_actual * cantidad_a_vender #Total sin incluir comisión
    comision = calcular_comision(monto_total)
    return monto_total - comision

"Validación de portafolio, cantidad suficiente, horario y frescura del precio para venta de acciones"
def validar_transaccion_venta(portafolio, simbolo_accion, cantidad_a_vender, precio_actual, timestamp_precio):
    if not mercado_abierto():
        return False, "Mercado cerrado. Solo se permite visualización.", 0
    if not es_precio_valido(timestamp_precio):
        return False, "Precio desactualizado. Esperando actualización.", 0
    if simbolo_accion not in portafolio:
        return False, f"No tienes acciones de {simbolo_accion} en tu portafolio.", 0

    cantidad_poseida = portafolio[simbolo_accion]['cantidad']
    if cantidad_a_vender > cantidad_poseida:
        return False, f"No puedes vender {cantidad_a_vender}. Solo posees {cantidad_poseida}.", 0

    monto_a_recibir = calcular_monto_a_recibir(precio_actual, cantidad_a_vender)
    return True, f"Venta exitosa. Recibes: ${monto_a_recibir:.2f}", monto_a_recibir  

"Calcula el porcentaje de ganancia o pérdida de una inversión."
def calcular_rendimiento(precio_compra, precio_actual):
    rendimiento = ((precio_actual - precio_compra) / precio_compra) * 100
    return round(rendimiento, 2)
