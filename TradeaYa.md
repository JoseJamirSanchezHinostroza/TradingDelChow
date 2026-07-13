**Universidad Nacional Mayor de San Marcos** 

**FACULTAD:** Facultad de Ingeniería

de Sistemas e Informática

**ASIGNATURA:** Algorítmica I

**TEMA:** Primer Entregable del Proyecto

Final

**DOCENTE: Gustavo Arredondo Castillo**

**GRUPO:**

Sanchez Hinostroza, Jose Jamir

Abad Cuva, David Eduardo

ErazoRamirez Castrejón, Jeremi Josué

2026

TradeaYa! - PeruDevs

1\. Descripción de las funcionalidades del proyecto:

TradeaYa! es una aplicación que permite al usuario interactuar con el mercado de acciones de EE.UU a través de un simulador de bolsa de valores en tiempo real. En esta app, es posible visualizar los precios de las acciones más relevantes del mercado (Apple, Tesla, etc.) en tiempo real y operar sobre ellas con dinero ficticio gracias a Alpaca API.

Además, implementamos Yahoo Finance API, cuya función es proporcionar los datos históricos de dichas acciones. Así, el usuario obtiene la experiencia completa: analiza el comportamiento histórico de las acciones, revisa el precio actual de la acción de su interés y compra/vende utilizando dinero ficticio.

TradeaYa! es el simulador definitivo para futuros traders: permite desarrollar estrategias de inversión sin riesgo financiero real.

2\. Reglas del Negocio:

Se implementarán las siguientes reglas en el proyecto, de manera que puedan asegurar el correcto funcionamiento del mismo.

● Validación de Saldo: El sistema no permitirá compras si el costo total de la transacción (precio de acción x cantidad) más la comisión excede el saldo disponible en la cuenta ficticia. A esa liquidez también se le restaría lo ya usado para otras transacciones en ordenes de compras pendientes.

● Gestión de Comisiones: Se aplicará una comisión fija o porcentual por cada operación realizada (ej. 0.5% por transacción) para simular los costos operativos de un broker real. No obstante, el precio de comisión podría bajar si el volumen comprado es amplio.

● Horario de Mercado: Las operaciones de compra/venta solo se procesarán si el mercado de EE. UU. está abierto (Lunes a Viernes, 9:30 AM - 4:00 PM EST). Fuera de este horario, el sistema solo permitirá la visualización. El sistema, sin embargo, podría permitir almacenar órdenes de compra para ejecutarlas tan pronto como el mercado vuelva a abrirse.

● Propiedad de Activos: El usuario sólo podrá vender acciones que existan previamente en su portafolio y en cantidades iguales o menores a las que posee. ● Actualización de Precios: Los precios de mercado deben refrescarse con una latencia máxima definida (ej. cada 15-60 segundos) para asegurar que la toma de decisiones se base en datos recientes.

Además, el proyecto podría incluir también las funciones de educación de inversión con salvaguardas específicos:

● Ejecución de Órdenes: El programa podría enseñar al usuario a ordenar la compra de acciones si es que el precio va debajo o sobre límites que se establecieron en la misma orden.

● Gestión de riesgo: Si la Ejecución de órdenes no está activada, cuando el precio cae por debajo de un cierto límite, el sistema vendería automáticamente para proteger capital y tiraría una advertencia respecto a esto. En contrapunto, si sube por encima

de un porcentaje, el sistema empezará a sugerir vender para obtener ganancias, y vendería automáticamente si empieza a caer para asegurar ganancias. ● Diversificación de Portafolio: El sistema no permitirá que una sola acción represente más del 30% del valor total de la cuenta

3\. Distribución del desarrollo por integrante:

● Abad David(BackEnd): Se encargará del servidor y la gestión de datos necesarios para operar, además de establecer y mantener la conexión con las API's de Alpaca y Yahoo Finance.

● Ramirez Jeremi(FrontEnd): Se encargará de la parte gráfica y la experiencia de usuario (UX/UI). Su objetivo es presentar una interfaz gráfica intuitiva, moderna y atractiva para el consumidor, graficando datos historícos de manera clara.

● Sánchez José(Algoritmos): Se encargará de la lógica central de la aplicación. Traducirá las reglas del negocio en código y creará algoritmos matemáticos que calculen comisiones, validen saldos y gestionen el portafolio ficticio del usuario de forma precisa.

4\. Códigos:

La comunicación entre ambos archivos funciona mediante una relación de solicitud y respuesta: el Frontend “interfaz.py” actúa como el centro de mando que recibe las órdenes del usuario y, cada vez que necesita datos reales o realizar una operación, llama a funciones específicas del Backend “conexion_api.py”. El Backend procesa esa petición conectándose a internet, obtiene la información y se la devuelve al Frontend para que este la valide con sus reglas de negocio y la muestre en pantalla. Es un intercambio constante donde el Frontend decide qué y cuándo hacer algo, mientras que el Backend es el encargado de cómo obtener los datos técnicos del mercado. A continuación, los códigos para el frontend y el backend:

Frontend (interfaz.py):

import os

import sys

from conexion_api import TradeEngine

class TradeYaCLI:

def \__init_\_(self):

self.engine = TradeEngine()

self.usuario = "PeruDev"

self.comision = 0.005 # 0.5%

self.prompt = f"PS C:\\\\Users\\\\{self.usuario}\\\\TradeaYa> "

def limpiar_pantalla(self):

os.system('cls' if os.name == 'nt' else 'clear')

def imprimir_bienvenida(self):

print("TradeaYa! Shell \[Versión 1.0.2026\]")

print("(c) PeruDevs Corporation. Todos los derechos reservados.\\n") print("Comandos: saldo, precio &lt;ticker&gt;, comprar &lt;ticker&gt; &lt;cant&gt;, clear, exit\\n")

def ejecutar(self):

self.limpiar_pantalla()

self.imprimir_bienvenida()

while True:

\# Captura la entrada del usuario simulando el prompt de PowerShell entrada = input(self.prompt).strip().lower().split()

if not entrada:

continue

comando = entrada\[0\]

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

print("Error: Debe especificar un ticker. Uso: precio &lt;ticker&gt;") continue

ticker = entrada\[1\].upper()

precio = self.engine.obtener_precio_actual(ticker)

print(f"{ticker} -> ${precio}")

elif comando == "comprar":

if len(entrada) < 3:

print("Error: Uso: comprar &lt;ticker&gt; &lt;cantidad&gt;")

continue

ticker = entrada\[1\].upper()

try:

cantidad = int(entrada\[2\])

precio_u = self.engine.obtener_precio_actual(ticker)

if isinstance(precio_u, str):

print(f"Error: {precio_u}")

continue

\# Lógica de Algoritmos (Regla de Negocio)

costo_base = precio_u \* cantidad

total_con_comision = costo_base \* (1 + self.comision) saldo_actual = self.engine.obtener_saldo()

if total_con_comision > saldo_actual:

print(f"Fondos insuficientes. Requerido: ${total_con_comision:.2f}") else:

print(f"Ejecutando orden por ${total_con_comision:.2f}...") res = self.engine.comprar_accion(ticker, cantidad) print(res)

except ValueError:

print("Error: La cantidad debe ser un número entero.")

else:

print(f"'{comando}' no se reconoce como un comando interno.")

if \__name__ == "\__main_\_":

app = TradeYaCLI()

app.ejecutar()

Backend(conexion_api.py):

import alpaca_trade_api as tradeapi

import os

import yfinance as yf

from dotenv import load_dotenv

load_dotenv()

class TradeEngine:

def \__init_\_(self):

\# Conexión interna

self.key = os.getenv('ALPACA_KEY')

self.secret = os.getenv('ALPACA_SECRET')

self.endpoint = os.getenv('ALPACA_ENDPOINT')

self.api = tradeapi.REST(self.key, self.secret, self.endpoint, api_version='v2')

def obtener_saldo(self):

"""Devuelve el dinero disponible en la cuenta."""

try:

account = self.api.get_account()

return float(account.cash)

except Exception as e:

return f"Error: {e}"

def obtener_precio_actual(self, simbolo):

"""Busca el precio de una acción (ej: 'AAPL' para Apple).""" try:

\# Se usa yfinance para datos rápidos de mercado ticker = yf.Ticker(simbolo)

precio = ticker.history(period='1d')\['Close'\].iloc\[-1\] return round(precio, 2)

except Exception:

return "No se encontró el símbolo"

def comprar_accion(self, simbolo, cantidad):

"""Ejecuta una orden de compra real en el simulador.""" try:

self.api.submit_order(

symbol=simbolo,

qty=cantidad,

side='buy',

type='market',

time_in_force='gtc'

)

return f"Compra exitosa de {cantidad} acciones de {simbolo}" except Exception as e:

return f"Error en la compra: {e}"

\# Condicional

if \__name__ == "\__main_\_":

\# Creamos el objeto del motor

motor = TradeEngine()

\# Probamos la conexión obteniendo el saldo

saldo = motor.obtener_saldo()

print(f" ¡Conexión exitosa! Saldo actual: ${saldo}")

\# Probamos buscando el precio de una acción

precio_apple = motor.obtener_precio_actual('AAPL') print(f" Precio actual de Apple (AAPL): ${precio_apple}")