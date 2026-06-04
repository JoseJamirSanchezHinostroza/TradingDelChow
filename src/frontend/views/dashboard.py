"""
frontend/views/dashboard.py - TradeaYa!
Graficación de la terminal de inversión: consulta de precios, compra/venta y resumen de portafolio.
"""

import time # Librería de tiempo
import pandas as pd # Pandas para tablas de datos
import streamlit as st # Streamlit como motor gráfico de la página web

# ─────────────────────────────────────────────────────────
# FUNCIÓN QUE DIBUJA LA PANTALLA
# ─────────────────────────────────────────────────────────

def mostrar_pantalla_dashboard() -> None:
    sesion = st.session_state.sesion # Extrae de Streamlit el objeto de la sesión
    motor  = st.session_state.motor # // el motor de Yahoo Finance
    db     = st.session_state.db # // la base de datos
    u_id   = st.session_state.usuario_id # // el ID de usuario

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

    col_izq, col_der = st.columns([1, 2]) # División de la página en 2 columnas (derecha es el doble de ancha que la izquierda)

    # ── Columna izquierda: Todo lo que aparecerá ───────────────────────────────────────
    with col_izq:
        st.subheader("⚡ Operaciones")

        simbolo      = st.text_input("Ticker (ej: AAPL, TSLA, NVDA):").strip().upper() # Caja de texto para ingresar Ticker (quita espacios y pone mayúsculas automáticamente)
        cantidad     = st.number_input("Cantidad:", min_value=1, step=1) # Caja de números para colocar la cantidad de acciones a operar (números forzadamente positivos y enteros)
        precio_actual = 0.0

        if simbolo: # Si el usuario escribe un Ticker
            with st.spinner(f"Consultando mercado: {simbolo}..."): # Rueda de carga para búsqueda del precio
                precio_actual = motor.obtener_precio_actual(simbolo) # Va a Yahoo Finance a obtener el precio con la función del BackEnd

            if precio_actual: # Si lo obtiene...
                st.metric(label=f"Precio Actual {simbolo}", value=f"${precio_actual:,.2f}") # Muestra el precio encontrado
                _mostrar_grafico(motor, simbolo) # Gráfico de los precios históricos (último mes)
            else: # Si no...
                st.error("Símbolo no encontrado o error de conexión.")

        col_compra, col_venta = st.columns(2) # Divide la columna izquierda en 2 botones de compra / venta

        with col_compra:
            if st.button("🟩 COMPRAR", use_container_width=True): # Si presionas el botón VENDER
                _ejecutar_compra(sesion, db, u_id, simbolo, cantidad, precio_actual)

        with col_venta:
            if st.button("🟥 VENDER", use_container_width=True): # Si presionas el botón VENDER
                _ejecutar_venta(sesion, db, u_id, simbolo, cantidad, precio_actual)

    # ── Columna derecha: Portafolio ───────────────────────────────────────────
    with col_der:
        st.subheader("📊 Mi Portafolio")
        _mostrar_portafolio(sesion, motor)

    # ── Historial de operaciones (abajo) ──────────────────────────────────────────────
    with st.expander("📜 Ver Historial de Operaciones"):
        _mostrar_historial(db, u_id)


# ─────────────────────────────────────────────────────────
# Gráfico de precios históricos: pide a Yahoo Finance
# ─────────────────────────────────────────────────────────

"""Muestra el gráfico de tendencia del último mes. Recibe el motor de la API y el Ticker"""
def _mostrar_grafico(motor, simbolo: str) -> None:
    
    st.markdown(f"### 📈 Tendencia: {simbolo}")
    
    try:
        datos_hist = motor.obtener_datos_grafico(simbolo, periodo="1mo") # Petición al motor de precios el historial del último mes
        if datos_hist: # Si existen los datos
            serie = pd.Series(datos_hist) # Conversión de datos crudos a una columna Pandas de datos
            serie.index = pd.to_datetime(serie.index).date # Recorta las fechas para el eje X (solo día)
            
            variacion = ((serie.iloc[-1] - serie.iloc[0]) / serie.iloc[0]) * 100 # Cálculo de la variacion de precios entre hoy[-1] y hace 1 mes[0]
            
            st.metric(
                label="Precio respecto al mes anterior", 
                value=f"${serie.iloc[-1]:,.2f}", 
                delta=f"${serie.iloc[-1]-serie.iloc[0]:,.2f} ({variacion:+.2f}%)" # Variación entre hace 1 mes y hoy en absoluto y porcentaje
            )

            st.area_chart(serie, color="#29b5e8") # Gráfico con relleno de color celeste

            st.caption(f"Variación del último mes: **{variacion:+.2f}%**") # Muestra la variación en porcentaje y con signo (+.2f)
        else:
            st.warning(f"Sin historial disponible para {simbolo}.") # No hay datos
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
        st.success(f"✅ Compra de {cantidad} × {simbolo} guardada.")
        time.sleep(1) # Congela el programa 1 segundo para leer el mensaje de éxito
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
            st.success(f"✅ Venta registrada. {msg}")
            time.sleep(1) # Congela el programa 1 segundo para leer el mensaje de éxito
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
        st.info("Tu portafolio está vacío. ¡Empieza a tradear!") # Si no hay acciones


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
        st.info("Aún no has realizado ninguna operación.") # Si no hay opetaciones

