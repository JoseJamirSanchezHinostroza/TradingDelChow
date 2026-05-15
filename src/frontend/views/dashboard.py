"""
frontend/views/dashboard.py - TradeaYa!
Terminal de inversión: consulta de precios, compra/venta y resumen de portafolio.
"""

import time

import pandas as pd
import streamlit as st


def mostrar_pantalla_dashboard() -> None:
    sesion = st.session_state.sesion
    motor  = st.session_state.motor
    db     = st.session_state.db
    u_id   = st.session_state.usuario_id

    # ── Sincronización inicial con la DB ──────────────────────────────────────
    # Se ejecuta una sola vez por sesión para cargar saldo y portafolio reales.
    if "db_sincronizada" not in st.session_state:
        with db.conectar() as conn:
            fila = conn.execute(
                "SELECT saldo FROM usuarios WHERE id = ?", (u_id,)
            ).fetchone()
            if fila:
                sesion.saldo = fila[0]

        sesion.portafolio = db.obtener_portafolio(u_id)
        st.session_state.db_sincronizada = True

    # ── Barra lateral ─────────────────────────────────────────────────────────
    st.sidebar.title("Mi Perfil")
    st.sidebar.write(f"👤 **{st.session_state.usuario_nombre}**")
    st.sidebar.write(f"💼 ID Cuenta: #{u_id}")

    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.usuario_id = None
        st.session_state.pop("db_sincronizada", None)
        st.rerun()

    # ── Encabezado ────────────────────────────────────────────────────────────
    st.title("📈 TradeaYa! | Terminal de Inversión")
    st.markdown("---")

    col_izq, col_der = st.columns([1, 2])

    # ── Columna izquierda: operaciones ───────────────────────────────────────
    with col_izq:
        st.subheader("⚡ Operaciones")

        simbolo      = st.text_input("Ticker (ej: AAPL, TSLA, NVDA):").strip().upper()
        cantidad     = st.number_input("Cantidad:", min_value=1, step=1)
        precio_actual = 0.0

        if simbolo:
            with st.spinner(f"Consultando mercado: {simbolo}..."):
                precio_actual = motor.obtener_precio_actual(simbolo)

            if precio_actual:
                st.metric(label=f"Precio Actual {simbolo}", value=f"${precio_actual:,.2f}")
                _mostrar_grafico(motor, simbolo)
            else:
                st.error("Símbolo no encontrado o error de conexión.")

        # Botones de compra / venta
        col_compra, col_venta = st.columns(2)

        with col_compra:
            if st.button("🟩 COMPRAR", use_container_width=True):
                _ejecutar_compra(sesion, db, u_id, simbolo, cantidad, precio_actual)

        with col_venta:
            if st.button("🟥 VENDER", use_container_width=True):
                _ejecutar_venta(sesion, db, u_id, simbolo, cantidad, precio_actual)

    # ── Columna derecha: portafolio ───────────────────────────────────────────
    with col_der:
        st.subheader("📊 Mi Portafolio")
        _mostrar_portafolio(sesion, motor)

    # ── Historial de operaciones ──────────────────────────────────────────────
    with st.expander("📜 Ver Historial de Operaciones"):
        _mostrar_historial(db, u_id)


# ─────────────────────────────────────────────────────────
# HELPERS PRIVADOS
# ─────────────────────────────────────────────────────────

def _mostrar_grafico(motor, simbolo: str) -> None:
    """Muestra el gráfico de tendencia del último mes."""
    st.markdown(f"### 📈 Tendencia: {simbolo}")
    try:
        datos_hist = motor.obtener_datos_grafico(simbolo, periodo="1mo")
        if datos_hist:
            serie = pd.Series(datos_hist)
            serie.index = pd.to_datetime(serie.index).date
            st.area_chart(serie, color="#29b5e8")

            variacion = ((serie.iloc[-1] - serie.iloc[0]) / serie.iloc[0]) * 100
            st.caption(f"Variación del último mes: **{variacion:+.2f}%**")
        else:
            st.warning(f"Sin historial disponible para {simbolo}.")
    except Exception as e:
        st.error(f"Error procesando gráfico: {e}")


def _ejecutar_compra(sesion, db, u_id: int, simbolo: str, cantidad: int, precio_actual: float) -> None:
    """Valida y ejecuta una compra, persistiendo en DB."""
    if precio_actual <= 0:
        st.error("Obtén el precio del ticker antes de comprar.")
        return

    costo_total = precio_actual * cantidad
    if sesion.saldo < costo_total:
        st.error("Saldo insuficiente.")
        return

    nuevo_saldo = sesion.saldo - costo_total
    if db.guardar_compra(u_id, simbolo, cantidad, precio_actual, nuevo_saldo):
        sesion.comprar(simbolo, cantidad, precio_actual, time.time())
        st.success(f"✅ Compra de {cantidad} × {simbolo} guardada.")
        time.sleep(1)
        st.rerun()
    else:
        st.error("Error al guardar la compra en la base de datos.")


def _ejecutar_venta(sesion, db, u_id: int, simbolo: str, cantidad: int, precio_actual: float) -> None:
    """Valida y ejecuta una venta, persistiendo en DB."""
    exito, msg = sesion.vender(simbolo, cantidad, precio_actual, time.time())

    if exito:
        if db.guardar_venta(u_id, simbolo, cantidad, precio_actual, sesion.saldo):
            st.success(f"✅ Venta registrada. {msg}")
            time.sleep(1)
            st.rerun()
        else:
            st.error("Error al guardar la venta en la base de datos.")
    else:
        st.error(msg)


def _mostrar_portafolio(sesion, motor) -> None:
    """Muestra métricas y tabla de posiciones abiertas."""
    precios_vivos = {
        s: p
        for s in sesion.portafolio
        if (p := motor.obtener_precio_actual(s)) is not None
    }

    resumen = sesion.get_resumen(precios_vivos)

    k1, k2, k3 = st.columns(3)
    k1.metric("Saldo Disponible",  f"${resumen['saldo_disponible']:,.2f}")
    k2.metric("Valor Acciones",    f"${resumen['valor_portafolio']:,.2f}")
    k3.metric("Patrimonio Total",  f"${resumen['patrimonio_total']:,.2f}")

    st.markdown("---")

    if resumen["posiciones"]:
        st.write("### Posiciones Abiertas")

        df = pd.DataFrame(resumen["posiciones"]) #Crear el DataFrame
        
        #Renombrar columnas para mejor presentación
        df = df.rename(columns={
            "simbolo": "Símbolo",
            "cantidad": "Cantidad",
            "precio_compra": "Precio Promedio",
            "precio_actual": "Precio Actual",
            "rendimiento_%": "Rendimiento"
        })

        df.index = range(1, len(df) + 1) #Ajuste de índice de enumeración de posiciones

        # Mostrar tabla con formato de moneda y porcentaje
        st.dataframe(
            df.style.format({
                "Precio Promedio" : "${:.2f}",
                "Precio Actual" : "${:.2f}",
                "Rendimiento" : "{:.2f}%",
            }),
            use_container_width=True,
        )

    else:
        st.info("Tu portafolio está vacío. ¡Empieza a tradear!")


def _mostrar_historial(db, u_id: int) -> None:
    """Muestra el historial completo de transacciones del usuario."""
    historial = db.obtener_historial(u_id)
    if historial:
        df = pd.DataFrame(historial, columns=["Acción", "Tipo", "Cantidad", "Precio", "Fecha"])
        df.index = range(len(df), 0, -1)
        st.dataframe(
            df.style.format({
                "Precio": "${:.2f}"
            }),
            use_container_width=True
        )
    else:
        st.info("Aún no has realizado ninguna operación.")
