"""
frontend/views/dashboard.py - TradeaYa!
Terminal de inversión: portafolio, compra/venta y predicción ML.
Los precios, gráficos y métricas se actualizan automáticamente cada 60 s
mediante st.fragment(run_every=60) definidos en helpers/precio_live.py.
El sidebar completo (usuario, saldo, reloj/estado de mercado NY, logout)
se construye íntegramente en helpers/sidebar.py; este archivo solo lo invoca.
"""

import streamlit as st

from views.helpers.precio_live import (
    grafico_portafolio_live,
    grafico_inversion_live,
)
from views.helpers.auxiliares import (
    _mostrar_historial,
    _obtener_todos_los_tickers,
)
from views.helpers.sidebar import _renderizar_sidebar
from views.helpers.prediccion import mostrar_pantalla_prediccion


# ─────────────────────────────────────────────────────────
# HEADER PRINCIPAL
# ─────────────────────────────────────────────────────────

def _renderizar_header() -> None:
    st.markdown("""
    <div style="display:flex;align-items:baseline;gap:0.7rem;margin-bottom:0.2rem;">
        <span style="font-size:1.5rem;">📈</span>
        <span style="font-family:'Inter',sans-serif;font-size:1.5rem;font-weight:700;
                     color:#e0e6f0;letter-spacing:-0.02em;">TradeaYa!</span>
        <span style="font-size:0.7rem;font-weight:500;letter-spacing:0.1em;
                     text-transform:uppercase;color:#00b4d8;
                     background:rgba(0,180,216,0.08);border:1px solid rgba(0,180,216,0.2);
                     border-radius:4px;padding:0.15rem 0.5rem;
                     margin-left:0.2rem;align-self:center;">Terminal</span>
    </div>
    <p style="font-size:0.75rem;color:#3a4f63;letter-spacing:0.06em;
              text-transform:uppercase;margin:0 0 1rem;">
        Simulación con datos reales de mercado</p>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# PESTAÑA PORTAFOLIO
# ─────────────────────────────────────────────────────────

def _tab_portafolio(sesion, motor, db, u_id: int) -> None:

    # Fragmento live: métricas + tabla + selector + gráfico
    # (todo en el orden correcto, se refresca cada 60 s)
    grafico_portafolio_live(motor, sesion)

    st.markdown("---")
    with st.expander("📜 Historial de operaciones"):
        _mostrar_historial(db, u_id)


# ─────────────────────────────────────────────────────────
# PESTAÑA ZONA DE INVERSIÓN
# ─────────────────────────────────────────────────────────

def _tab_inversion(sesion, motor, db, u_id: int, lista_tickers: list) -> None:

    # ── Buscador ──────────────────────────────────────────────────────────────
    st.markdown("""
    <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;
              text-transform:uppercase;color:#7b8fa6;margin-bottom:0.5rem;">
    Buscador de mercado</p>
    """, unsafe_allow_html=True)

    col_bus, col_man = st.columns([2, 1])
    with col_bus:
        opcion = st.selectbox(
            "Ticker", ["OTRO..."] + lista_tickers,
            label_visibility="collapsed",
        )
    with col_man:
        if opcion == "OTRO...":
            simbolo_inv = st.text_input(
                "Ticker manual", placeholder="Ej: AAPL",
                label_visibility="collapsed",
            ).strip().upper()
        else:
            simbolo_inv = opcion
            st.markdown(f"""
            <div style="background-color:#0d1b2a;border:1px solid #1c2f45;
                        border-radius:6px;padding:0.45rem 0.8rem;
                        font-family:'JetBrains Mono',monospace;font-size:0.9rem;
                        color:#00b4d8;font-weight:500;">{simbolo_inv}</div>
            """, unsafe_allow_html=True)

    # ── Panel del ticker ──────────────────────────────────────────────────────
    if simbolo_inv:
        # Selector de periodo — fuera del fragmento (input del usuario)
        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)
        periodo_inv = st.radio(
            "Rango", ["1d", "1mo", "1y"],
            format_func=lambda x: {"1d": "1 Día", "1mo": "1 Mes", "1y": "1 Año"}[x],
            horizontal=True, key="radio_inv",
            label_visibility="collapsed",
        )

        # Fragmento live: gráfico + precio + calculadora + botones (todo refresca cada 60 s)
        grafico_inversion_live(motor, simbolo_inv, periodo_inv, sesion, db, u_id)


# ─────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────

def mostrar_pantalla_dashboard() -> None:
    sesion = st.session_state.sesion
    motor  = st.session_state.motor
    db     = st.session_state.db
    u_id   = st.session_state.usuario_id

    # Sincronización inicial única con la DB (se ejecuta solo la primera vez)
    if "db_sincronizada" not in st.session_state:
        with db.conectar() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT saldo FROM usuarios WHERE id = ?".replace(
                    "?", "%s" if db.en_cloud else "?"
                ),
                (u_id,),
            )
            fila = cur.fetchone()
            if fila:
                sesion.saldo = fila[0]
        sesion.portafolio = db.obtener_portafolio(u_id)
        st.session_state.db_sincronizada = True

    lista_tickers = _obtener_todos_los_tickers()

    # El sidebar completo se construye en helpers/sidebar.py; aquí solo se invoca.
    _renderizar_sidebar(sesion, motor, u_id)
    _renderizar_header()

    tab_port, tab_inv, tab_pred = st.tabs([
        "📊  Portafolio",
        "⚡  Zona de Inversión",
        "🤖  Predicción ML",
    ])

    with tab_port:
        _tab_portafolio(sesion, motor, db, u_id)

    with tab_inv:
        _tab_inversion(sesion, motor, db, u_id, lista_tickers)

    with tab_pred:
        mostrar_pantalla_prediccion(lista_tickers)