"""
frontend/views/dashboard.py - TradeaYa!
Graficación de la terminal de inversión: consulta de precios, compra/venta y resumen de portafolio.
"""

import time # Librería de tiempo
import pandas as pd # Pandas para tablas de datos
import streamlit as st # Streamlit como motor gráfico de la página web
from yahoo_fin import stock_info as si # Yahoo Finance para obtener Tickers

# ─────────────────────────────────────────────────────────
# FUNCIÓN QUE OBTIENE TODOS LOS TICKERS DISPONIBLES DEL MERCADO
# ─────────────────────────────────────────────────────────
@st.cache_data(ttl=86400) # Se guarda en caché por 24 horas para priorizar velocidad

def _obtener_todos_los_tickers() -> list: # Descarga los Tickers del ecosistema Yahoo Finance
    try:
        nasdaq = si.tickers_nasdaq()
        sp500 = si.tickers_sp500()
        dow = si.tickers_dow()

        todos_los_tickers = list(set(nasdaq + sp500 + dow)) # Unión de las listas y eliminación de duplicados con set()
        todos_limpios = [str(t).upper() for t in todos_los_tickers if pd.notna(t)]

        return sorted(todos_limpios) # Retorna la lista ordenada alfabéticamente
    
    except Exception as e:
        st.error(f"Error al obtener los tickers: {e}")
        return ["AAPL", "AMD", "AMZN", "MSFT", "NVDA", "TSLA"] # Lista de Tickers respaldo por si falta Internet

# ─────────────────────────────────────────────────────────
# FUNCIÓN QUE DIBUJA LA PANTALLA
# ─────────────────────────────────────────────────────────

def mostrar_pantalla_dashboard() -> None:
    sesion = st.session_state.sesion # Extrae de Streamlit el objeto de la sesión
    motor  = st.session_state.motor # // el motor de Yahoo Finance
    db     = st.session_state.db # // la base de datos
    u_id   = st.session_state.usuario_id # // el ID de usuario

    lista_completa_tickers = _obtener_todos_los_tickers() # Instantáneo por el caché
    
    if "db_sincronizada" not in st.session_state: # Sincronización inicial y única con la DB por sesión para cargar saldo y portafolio
        with db.conectar() as conn: # Abre la DataBase
            fila = conn.execute( # Extrae el saldo del usuario de la tabla usuarios
                "SELECT saldo FROM usuarios WHERE id = ?", (u_id,)
            ).fetchone()
            if fila: # Si existe el usuario, extrae su saldo a la memoria de la sesión presente
                sesion.saldo = fila[0]

        sesion.portafolio = db.obtener_portafolio(u_id) # Extrae las acciones de la DB a la memoria de la sesión
        st.session_state.db_sincronizada = True # Sincronización completa --> Este bloque de código NO se volverá a ejecutar

    # ── Barra lateral: Perfil-Nombre-ID ─────────────────────────────────────────────────────────
    st.sidebar.title("Mi Perfil")
    st.sidebar.write(f"👤 **{st.session_state.usuario_nombre}**")
    st.sidebar.write(f"💼 ID Cuenta: #{u_id}")

    if st.sidebar.button("Cerrar Sesión"): # Si el usuario presiona el botón de CERRAR SESIÓN...
        st.session_state.usuario_id = None # Borra el usuario de la memoria
        st.session_state.pop("db_sincronizada", None) # Borra la sincronización de la memoria
        st.rerun() # Recarga de página

    # ── Encabezado: Título principal de la página ────────────────────────────────────────────────────────────
    st.title("📈 TradeaYa! | Terminal de Inversión")
    st.markdown("---")

    tab_portafolio, tab_inversion = st.tabs(["📊 Mi Portafolio", "⚡ Zona de Inversión"]) # División de la página en 2 pestañas
    
    # ─────────────────────────────────────────
    # PESTAÑA DE PORTAFOLIO
    # ─────────────────────────────────────────
    with tab_portafolio:
        st.subheader("Resumen de tu cuenta")
        _mostrar_portafolio(sesion, motor) # Gráfico del portafolio
        st.markdown("---")

        if sesion.portafolio: # Si el portafolio no está vacío, muestra el historial de operaciones
            st.subheader("Análisis de mis acciones")
            col_sel, col_per = st.columns([2, 1]) # División en 2 columnas: selección de acción y gráfico de precios
            
    # ── Columnas ───────────────────────────────────────────       
            with col_sel:
                accion_seleccionada = st.selectbox(
                    "Selecciona una acción de tu portafolio:", 
                    list(sesion.portafolio.keys())
                )

            with col_per:
                periodo_portafolio = st.radio(
                    "Rango de tiempo:", 
                    ["1d", "1mo", "1y"], 
                    format_func=lambda x: {"1d": "1 Día", "1mo": "1 Mes", "1y": "1 Año"}[x],
                    horizontal=True,
                    key="radio_port"
                )

            _mostrar_grafico(motor, accion_seleccionada, periodo_portafolio)

        st.markdown("---")
        with st.expander("📜 Ver Historial de Operaciones"):
            _mostrar_historial(db, u_id)

    # ─────────────────────────────────────────
    # PESTAÑA DE INVERSIÓN
    # ─────────────────────────────────────────
    with tab_inversion:
        st.subheader("Buscador de Mercado")

        opcion_busqueda = st.selectbox( # Selector inteligente que ofrece opciones de la lista o tipeo manual
            "Despliega la lista para seleccionar o elige 'OTRO...' para tipear libremente:",
            ["OTRO..."] + lista_completa_tickers
        )

        if opcion_busqueda == "OTRO...": # Tipeo manual del Ticker
            simbolo_inv = st.text_input("Escribe el Ticker de la acción de interés:").strip().upper()
        else:
            simbolo_inv = opcion_busqueda # Ticker de los recomendados

        if simbolo_inv:
            with st.spinner(f"Consultando mercado: {simbolo_inv}..."):
                precio_actual = motor.obtener_precio_actual(simbolo_inv) # Obtención del precio con la API
                if precio_actual:
                    periodo_inv = st.radio(
                        "Rango de tiempo:",
                        ["1d", "1mo", "1y"],
                        format_func=lambda x: {"1d": "1 día", "1mo": "1 mes", "1y": "1 año"}[x],
                        horizontal=True,
                        key="radio_inv"
                    )
                    _mostrar_grafico(motor, simbolo_inv, periodo_inv)

                    st.markdown("### 🛒 Calculadora de Operación")

                    # Layout de Valor - Cantidad - Total
                    c_valor, c_cant, c_total = st.columns(3)

                    with c_valor:
                        st.metric("Valor Actual", f"${precio_actual:,.2f}")
                    with c_cant:
                        cantidad = st.number_input("Cantidad de acciones:", min_value=1, step=1)
                    with c_total:
                        total_operacion = precio_actual * cantidad
                        st.metric("Total Calculado", f"${total_operacion:,.2f}")

                    # Botones
                    st.markdown("<br>", unsafe_allow_html=True) # Espacio extra
                    col_compra, col_venta = st.columns(2)

                    with col_compra:
                        if st.button("🟩 COMPRAR ACCIONES", use_container_width=True):
                            _ejecutar_compra(sesion, db, u_id, simbolo_inv, cantidad, precio_actual)

                    with col_venta:
                        if st.button("🟥 VENDER ACCIONES", use_container_width=True):
                            _ejecutar_venta(sesion, db, u_id, simbolo_inv, cantidad, precio_actual)

                else:
                    st.error(f"El símbolo '{simbolo_inv}' no fue encontrado en el mercado.") # Error de ticker inválido o fallo de la API

# ─────────────────────────────────────────────────────────
# Gráfico de precios históricos: pide a Yahoo Finance
# ─────────────────────────────────────────────────────────

"""Muestra el gráfico de tendencia del periodo seleccionado. Recibe el motor de la API, el Ticker y el Periodo"""
def _mostrar_grafico(motor, simbolo: str, periodo: str) -> None:
    
    nombres_periodo = {"1d": "Hoy (Intradía)", "1mo": "Último Mes", "1y": "Último Año"}
    
    try:
        datos_hist = motor.obtener_datos_grafico(simbolo, periodo=periodo) # Petición al motor de precios el historial del último mes
        if datos_hist: # Si existen los datos
            serie = pd.Series(datos_hist) # Conversión de datos crudos a una columna Pandas de datos
            if periodo == "1d":
                serie.index = pd.to_datetime(serie.index) # Intradía: muestra horas y minutos
            else:
                serie.index = pd.to_datetime(serie.index).date
            serie.index = pd.to_datetime(serie.index).date # Recorta las fechas para el eje X (solo día)
            
            variacion = ((serie.iloc[-1] - serie.iloc[0]) / serie.iloc[0]) * 100 # Cálculo de la variacion de precios entre hoy[-1] y hace 1 mes[0]
            
            st.metric( # Métrica dinámica sobre el gráfico que muestra el precio actual y la variación respecto al inicio del periodo
                label=f"Variación respecto al {nombres_periodo.get(periodo, 'periodo')}", 
                value=f"${serie.iloc[-1]:,.2f}", 
                delta=f"${serie.iloc[-1]-serie.iloc[0]:,.2f} ({variacion:+.2f}%)" # Variación entre hace 1 mes y hoy en absoluto y porcentaje
            )

            st.area_chart(serie, color="#29b5e8") # Gráfico con relleno de color celeste

        else:
            st.warning(f"Sin historial disponible para {simbolo} en el periodo '{periodo}'.") # No hay datos
    except Exception as e:
        st.error(f"Error procesando gráfico: {e}") # Fallo de la API/Internet

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

