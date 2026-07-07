"""
frontend/views/dashboard.py - TradeaYa!
Terminal de inversión: consulta de precios, compra/venta y resumen de portafolio.
"""

import time
import streamlit as st

from logic.calculos import calcular_comision

from views.helpers.precio_live  import (
    precio_portafolio_live,
    precio_ticker_live,
    precio_sidebar_live,
)
from views.helpers.auxiliares import (
    _mostrar_historial,
    _obtener_todos_los_tickers,
)
from views.helpers.grafico  import _mostrar_grafico
from views.helpers.prediccion       import mostrar_pantalla_prediccion


# ─────────────────────────────────────────────────────────
# BARRA LATERAL
# ─────────────────────────────────────────────────────────

def _renderizar_sidebar(sesion, motor, u_id: int) -> None:
    """Sidebar: perfil del usuario y saldo en tiempo real."""

    st.sidebar.markdown("""
    <div style="padding: 0.5rem 0 1.2rem;">
        <p style="
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #3a4f63;
            margin: 0 0 1rem;
        ">CUENTA ACTIVA</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"""
    <div style="
        background-color: #060d1f;
        border: 1px solid #1c2f45;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin-bottom: 1rem;
    ">
        <p style="
            font-size: 0.68rem;
            color: #3a4f63;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0 0 0.25rem;
        ">Usuario</p>
        <p style="
            font-size: 1rem;
            font-weight: 600;
            color: #e0e6f0;
            margin: 0 0 0.6rem;
        ">{st.session_state.usuario_nombre}</p>
        <p style="
            font-size: 0.68rem;
            color: #3a4f63;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0 0 0.2rem;
        ">ID de cuenta</p>
        <p style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            color: #7b8fa6;
            margin: 0;
        "># {u_id:06d}</p>
    </div>
    """, unsafe_allow_html=True)

    # Saldo disponible en sidebar — fragmento live (refresco cada 60 s)
    precio_sidebar_live(sesion)

    st.sidebar.markdown("---")

    # Estado del mercado
    from logic.calculos import mercado_abierto
    abierto = mercado_abierto()
    color_estado  = "#26a69a" if abierto else "#ef5350"
    texto_estado  = "MERCADO ABIERTO" if abierto else "MERCADO CERRADO"
    st.sidebar.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.6rem 0;
        margin-bottom: 0.8rem;
    ">
        <span style="
            width: 7px; height: 7px;
            background-color: {color_estado};
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 6px {color_estado};
        "></span>
        <span style="
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            color: {color_estado};
        ">{texto_estado}</span>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    if st.sidebar.button("Cerrar sesión", width="stretch"):
        st.session_state.usuario_id = None
        st.session_state.pop("db_sincronizada", None)
        # Limpiar uid de query_params para que no se restaure la sesión
        st.query_params.clear()
        st.rerun()


# ─────────────────────────────────────────────────────────
# HEADER PRINCIPAL
# ─────────────────────────────────────────────────────────

def _renderizar_header() -> None:
    """Cabecera de la terminal."""
    st.markdown("""
    <div style="
        display: flex;
        align-items: baseline;
        gap: 0.7rem;
        margin-bottom: 0.2rem;
    ">
        <span style="font-size: 1.5rem;">📈</span>
        <span style="
            font-family: 'Inter', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: #e0e6f0;
            letter-spacing: -0.02em;
        ">TradeaYa!</span>
        <span style="
            font-size: 0.7rem;
            font-weight: 500;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #00b4d8;
            background: rgba(0,180,216,0.08);
            border: 1px solid rgba(0,180,216,0.2);
            border-radius: 4px;
            padding: 0.15rem 0.5rem;
            margin-left: 0.2rem;
            align-self: center;
        ">Terminal</span>
    </div>
    <p style="
        font-size: 0.75rem;
        color: #3a4f63;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin: 0 0 1rem;
    ">Simulación con datos reales de mercado</p>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# PESTAÑA PORTAFOLIO
# ─────────────────────────────────────────────────────────

def _tab_portafolio(sesion, motor, db, u_id: int) -> None:

    precio_portafolio_live(sesion, motor)

    if sesion.portafolio:
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # Etiqueta de sección
        st.markdown("""
        <p style="
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #7b8fa6;
            margin: 1.2rem 0 0.6rem;
        ">Análisis de posición</p>
        """, unsafe_allow_html=True)

        col_sel, col_per = st.columns([2, 1])
        with col_sel:
            accion_seleccionada = st.selectbox(
                "Acción",
                list(sesion.portafolio.keys()),
                label_visibility="collapsed",
            )
        with col_per:
            periodo_portafolio = st.radio(
                "Periodo",
                ["1d", "1mo", "1y"],
                format_func=lambda x: {"1d": "1D", "1mo": "1M", "1y": "1A"}[x],
                horizontal=True,
                key="radio_port",
                label_visibility="collapsed",
            )

        _mostrar_grafico(motor, accion_seleccionada, periodo_portafolio, ctx="port")

    st.markdown("---")

    with st.expander("📜 Historial de operaciones"):
        _mostrar_historial(db, u_id)


# ─────────────────────────────────────────────────────────
# PESTAÑA ZONA DE INVERSIÓN
# ─────────────────────────────────────────────────────────

def _tab_inversion(sesion, motor, db, u_id: int, lista_tickers: list) -> None:

    # ── Buscador ──────────────────────────────────────────────────────────────
    st.markdown("""
    <p style="
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #7b8fa6;
        margin-bottom: 0.5rem;
    ">Buscador de mercado</p>
    """, unsafe_allow_html=True)

    col_bus, col_man = st.columns([2, 1])
    with col_bus:
        opcion_busqueda = st.selectbox(
            "Ticker",
            ["OTRO..."] + lista_tickers,
            label_visibility="collapsed",
        )
    with col_man:
        if opcion_busqueda == "OTRO...":
            simbolo_inv = st.text_input(
                "Ticker manual",
                placeholder="Ej: AAPL",
                label_visibility="collapsed",
            ).strip().upper()
        else:
            simbolo_inv = opcion_busqueda
            st.markdown(f"""
            <div style="
                background-color: #0d1b2a;
                border: 1px solid #1c2f45;
                border-radius: 6px;
                padding: 0.45rem 0.8rem;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.9rem;
                color: #00b4d8;
                font-weight: 500;
            ">{simbolo_inv}</div>
            """, unsafe_allow_html=True)

    # ── Panel del ticker ──────────────────────────────────────────────────────
    if simbolo_inv:
        # Selector de periodo (fuera del fragmento — solo cambia si el usuario lo toca)
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
        periodo_inv = st.radio(
            "Rango",
            ["1d", "1mo", "1y"],
            format_func=lambda x: {"1d": "1 Día", "1mo": "1 Mes", "1y": "1 Año"}[x],
            horizontal=True,
            key="radio_inv",
            label_visibility="collapsed",
        )

        _mostrar_grafico(motor, simbolo_inv, periodo_inv, ctx="inv")

        # Precio + calculadora + botones — fragmento live (refresco cada 60 s)
        precio_ticker_live(motor, simbolo_inv, sesion, db, u_id)


# ─────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────

def mostrar_pantalla_dashboard() -> None:
    sesion = st.session_state.sesion
    motor  = st.session_state.motor
    db     = st.session_state.db
    u_id   = st.session_state.usuario_id

    # Sincronización inicial única con la DB
    if "db_sincronizada" not in st.session_state:
        with db.conectar() as conn:
            fila = conn.execute(
                "SELECT saldo FROM usuarios WHERE id = ?", (u_id,)
            ).fetchone()
            if fila:
                sesion.saldo = fila[0]
        sesion.portafolio = db.obtener_portafolio(u_id)
        st.session_state.db_sincronizada = True

    lista_tickers = _obtener_todos_los_tickers()

    _renderizar_sidebar(sesion, motor, u_id)
    _renderizar_header()

    tab_portafolio, tab_inversion, tab_prediccion = st.tabs([
        "📊  Portafolio",
        "⚡  Zona de Inversión",
        "🤖  Predicción ML",
    ])

    with tab_portafolio:
        _tab_portafolio(sesion, motor, db, u_id)

    with tab_inversion:
        _tab_inversion(sesion, motor, db, u_id, lista_tickers)

    with tab_prediccion:
        mostrar_pantalla_prediccion(lista_tickers)