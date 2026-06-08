"""
frontend/views/dashboard.py - TradeaYa!
Graficación de la terminal de inversión: consulta de precios, compra/venta y resumen de portafolio.
"""

import time # Librería de tiempo
import pandas as pd # Pandas para tablas de datos
import streamlit as st # Streamlit como motor gráfico de la página web

from logic.calculos import calcular_comision

from views.helpers.auxiliares import (
    _ejecutar_compra,
    _ejecutar_venta,
    _mostrar_portafolio,
    _mostrar_historial,
    _obtener_todos_los_tickers
)

from views.helpers.grafico import (
    _mostrar_grafico
)

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
                        total_operacion=total_operacion+calcular_comision(total_operacion) # Comisión del 0.5%
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
