"""
frontend/views/helpers.py - TradeaYa!
Definición de funciones auxiliares para la construcción del Dashboard
"""

import time # Librería de tiempo
import pandas as pd # Pandas para tablas de datos
import streamlit as st # Streamlit como motor gráfico de la página web
import plotly.graph_objects as go # Plotly para gráficos avanzados de velas japonesas
from yahoo_fin import stock_info as si # Yahoo Finance para obtener Tickers


# ─────────────────────────────────────────────────────────
# FUNCIÓN QUE OBTIENE TODOS LOS TICKERS DISPONIBLES DEL MERCADO
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=86400) # Se guarda en caché por 24 horas para priorizar velocidad

def _obtener_todos_los_tickers() -> list: # Descarga los Tickers del servidor FileTransferProtocol público filtrada para compatibilizar con Yahoo Finance
    try:
        url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt"
        df = pd.read_csv(url, sep='|')

        df = df[df['Test Issue'] == 'N']
        tickers_crudos = df['Symbol'].dropna().astype(str).tolist()
        tickers_limpios = [t for t in tickers_crudos if t.isalpha() and len(t) <= 5] # Solo se conservan tickers alfabéticos hasta 5 letras

        return sorted(tickers_limpios) # Retorna la lista ordenada alfabéticamente
    
    except Exception as e:
        st.error(f"Error al obtener los tickers: {e}")
        return ["AAPL", "AMD", "AMZN", "MSFT", "NVDA", "TSLA"] # Lista de Tickers respaldo por si falta Internet
    

# ─────────────────────────────────────────────────────────
# Gráfico de precios históricos: pide a Yahoo Finance
# ─────────────────────────────────────────────────────────

"""Muestra el gráfico de tendencia del periodo seleccionado. Recibe el motor de la API, el Ticker y el Periodo"""
def _mostrar_grafico(motor, simbolo: str, periodo: str) -> None:
    
    nombres_periodo = {"1d": "Hoy (Intradía)", "1mo": "Último Mes", "1y": "Último Año"}
    
    try:
        datos_hist = motor.obtener_datos_grafico(simbolo, periodo=periodo) # Petición al motor de precios el historial del último mes
        
        if datos_hist is not None and (not datos_hist.empty if hasattr(datos_hist, 'empty') else datos_hist): # Si existen los datos
            
            if isinstance(datos_hist, dict): # Si el motor devuelve un diccionario o serie se convierte a DataFrame
                df = pd.DataFrame(list(datos_hist.items()), columns=["Fecha", "Close"]).set_index("Fecha")
            elif isinstance(datos_hist, pd.Series):
                df = datos_hist.to_frame(name="Close")
            else:
                df = datos_hist

            if periodo == "1d":
                df.index = pd.to_datetime(df.index) # Intradía: muestra horas y minutos
            else:
                df.index = pd.to_datetime(df.index).date # Recorta las fechas para el eje X (solo día)
            
            variacion = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100 # Cálculo de la variacion de precios entre hoy[-1] y hace 1 mes[0]
            
            st.metric( # Métrica dinámica sobre el gráfico que muestra el precio actual y la variación respecto al inicio del periodo
                label=f"Variación respecto al inicio del periodo {nombres_periodo[periodo]}", 
                value=f"${df['Close'].iloc[-1]:,.2f}", # Precio final del periodo
                delta=f"${df['Close'].iloc[-1]-df['Close'].iloc[0]:,.2f} ({variacion:+.2f}%)" # Variación en absoluto y porcentaje
            )

            fig = go.Figure # Gráfico de velas japonesas con Plotly

            if all(col in df.columns for col in ["Open", "High", "Low", "Close"]): # Si YFinance brinda el DF completo OHLC dibuja las velas
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    increasing_line_color='#26a69a', # Verde TradingView
                    decreasing_line_color='#ef5350', # Rojo TradingView
                    name="Velas"
                ))
            else:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df["Close"],
                    mode='lines+markers' if len(df) < 30 else 'lines', # Puntos si hay pocos datos
                    line=dict(color='#00b4d8', width=2.5),
                    marker=dict(color='#ffffff', size=5, line=dict(color='#00b4d8', width=2)), # Puntos blancos con borde cyan
                    name="Cierre"
                ))

            fig.update_layout( # Estilo profesional
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente para integración con Streamlit
                plot_bgcolor='#0b132b', # Azul oscuro profundo para el background del gráfico
                margin=dict(l=10, r=10, t=10, b=10),
                height=420,
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='#1c2541',       # Rejilla sutil azulada/neon
                    linecolor='#1c2541',
                    rangeslider=dict(visible=False) # Oculta la barra de abajo que quita espacio
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#1c2541', 
                    linecolor='#1c2541',
                    side='right'               # Precios a la derecha (Estándar de Pro-Trading)
                ),
                hovermode='x unified',
                showlegend=False
            )

            # Renderización en Streamlit
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.caption(f"Variación del periodo: **{variacion:+.2f}%**")

        else:
            st.warning(f"Sin historial disponible para {simbolo} en el periodo '{periodo}'.") # No hay datos
    except Exception as e:
        st.error(f"Error procesando gráfico profesional: {e}") # Fallo de la API/Internet

# ─────────────────────────────────────────────────────────
# Ejecución de Compra
# ─────────────────────────────────────────────────────────
"""Valida y ejecuta una compra, la guarda en DB. Recibe la sesión, DataBase, ID de usuario, Ticker, cantidad a comprar y precio actual."""
def _ejecutar_compra(sesion, db, u_id: int, simbolo: str, cantidad: int, precio_actual: float) -> None:
    
    if precio_actual <= 0: # Barrera por si el precio es inválido
        st.error("Obtén el precio del ticker antes de comprar.")
        return

    costo_total = precio_actual * cantidad # Cálculo del precio
    if sesion.saldo < costo_total: # Si el saldo de la sesión no alcanza
        st.error("Saldo insuficiente.")
        return

    nuevo_saldo = sesion.saldo - costo_total # Cálculo del saldo sobrante
    if db.guardar_compra(u_id, simbolo, cantidad, precio_actual, nuevo_saldo): # Intento de guardado de la compra en la DataBase
        sesion.comprar(simbolo, cantidad, precio_actual, time.time()) # Actualiza la memoria de la sesión: suma las acciones al portafolio
        st.toast(f"✅ Compra de {cantidad} × {simbolo} exitosa.", icon="🟩")
        time.sleep(1.5) # Congela el programa 1 segundo para leer el mensaje de éxito
        st.rerun() # Reinicio de pantalla: actualización de datos
    else:
        st.error("Error al guardar la compra en la base de datos.")


# ─────────────────────────────────────────────────────────
# Ejecución de Venta
# ─────────────────────────────────────────────────────────
"""Valida y ejecuta una venta, la guarda en DB. Recibe la sesión, DataBase, ID de usuario, Ticker, cantidad a vender y precio actual."""
def _ejecutar_venta(sesion, db, u_id: int, simbolo: str, cantidad: int, precio_actual: float) -> None:
    
    exito, msg = sesion.vender(simbolo, cantidad, precio_actual, time.time()) # La sesión define el éxito de la venta (cantidad suficiente)

    if exito:
        if db.guardar_venta(u_id, simbolo, cantidad, precio_actual, sesion.saldo): # Intento de guardado de la venta en la DataBase
            st.toast(f"✅ Venta registrada. {msg}", icon="🟥")
            time.sleep(1.5) # Congela el programa 1 segundo para leer el mensaje de éxito
            st.rerun() # Reinicio de pantalla: actualización de datos
        else:
            st.error("Error al guardar la venta en la base de datos.")
    else:
        st.error(msg) # Falta de acciones


# ─────────────────────────────────────────────────────────
# Gráfico del Portafolio:
# ─────────────────────────────────────────────────────────
"""Muestra la tabla de posiciones abiertas y sus métricas. Recibe la sesión y el motor de la API"""
def _mostrar_portafolio(sesion, motor) -> None:
    
    precios_vivos = { # Dictionary Comprehension: Creación de diccionarios (precios_vivos) a partir de iteración
        s: p # En cada iteración, s adoptará el nombre de una acción
        for s in sesion.portafolio # Recorre el inventario de acciones (portafolio)
        if (p := motor.obtener_precio_actual(s)) is not None # Llama a la API para obtener precios en vivo, guardados temporalmente en p (Operador Morsa :=). Se asegura de tomar precios no vacíos
    }

    resumen = sesion.get_resumen(precios_vivos) # Delega los precios frescos a la sesión para obtener el resumen: Ganancia o Pérdida
    costo_total = sum(p["cantidad"] * p["precio_compra"] for p in resumen["posiciones"]) # Lo que costaron las acciones actuales

    k1, k2, k3 = st.columns(3) # División en 3 bloques para los siguientes saldos y diferencias:
    k1.metric(
        label="Saldo Disponible",
        value=f"${resumen['saldo_disponible']:,.2f}"
    )
    k2.metric(
        label="Valor Acciones",
        value=f"${resumen['valor_portafolio']:,.2f}",
        delta=f"${resumen['valor_portafolio'] - costo_total:,.2f}" if costo_total > 0 else None # Diferencia entre el valor actual de las acciones menos lo que costaron
    )
    k3.metric(
        label="Patrimonio Total",
        value=f"${resumen['patrimonio_total']:,.2f}",
        delta=f"${resumen['patrimonio_total'] - 10000.00:,.2f} Total" # Diferencia entre el patrimonio actual e inicial
    )

    st.markdown("---")

    if resumen["posiciones"]: # Verifica la presencia de al menos 1 acción
        st.write("### Posiciones Abiertas")

        df = pd.DataFrame(resumen["posiciones"]) # Ingresa los datos en un DataFrame Pandas
        
        df = df.rename(columns={ # Renombra las columnas del resumen
            "simbolo": "Símbolo",
            "cantidad": "Cantidad",
            "precio_compra": "Precio Promedio",
            "precio_actual": "Precio Actual",
            "rendimiento_%": "Rendimiento"
        })

        df.index = range(1, len(df) + 1) #Ajuste de índice de enumeración (la posición más antigua empieza en 1)
        st.dataframe( # Mostrar tabla con formato de moneda ($) y porcentaje (%)
            df.style.format({
                "Precio Promedio" : "${:.2f}",
                "Precio Actual" : "${:.2f}",
                "Rendimiento" : "{:.2f}%",
            }),
            use_container_width=True, # Estira el ancho
        )

    else:
        st.info("Tu portafolio está vacío. ¡Empieza a tradear desde la Zona de Inversión!") # Si no hay acciones

# ─────────────────────────────────────────────────────────
# Gráfico del Historial de Operaciones
# ─────────────────────────────────────────────────────────
"""Muestra el historial completo de transacciones del usuario. Recibe la DataBase y el ID de usuario."""
def _mostrar_historial(db, u_id: int) -> None:
    
    historial = db.obtener_historial(u_id) # Extrae la información del usuario (ID) del DataBase
    if historial: # Si hay datos...
        df = pd.DataFrame(historial, columns=["Acción", "Tipo", "Cantidad", "Precio", "Fecha"]) # DataFrame de Pandas que ordena lso datos por columnas
        df.index = range(len(df), 0, -1) # Ajuste de índice de enumeración (la operación más antigua empieza por 1)
        st.dataframe( # Mostrar la columna Precio con formato de moneda ($)
            df.style.format({
                "Precio": "${:.2f}"
            }),
            use_container_width=True # Estira el ancho
        )
    else:
        st.info("Aún no has realizado ninguna operación. ¿Qué esperas?") # Si no hay opetaciones
