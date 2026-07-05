"""
frontend/views/dashboard.py - TradeaYa!
Terminal de inversión: consulta de precios, compra/venta y resumen de portafolio.
"""
from datetime import datetime
import pytz
import time
import streamlit as st

from logic.calculos import calcular_comision

from views.helpers.auxiliares import (
    _ejecutar_compra,
    _ejecutar_venta,
    _mostrar_portafolio,
    _mostrar_historial,
    _obtener_todos_los_tickers,
)
from views.helpers.grafico  import _mostrar_grafico
from views.prediccion       import mostrar_pantalla_prediccion


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

    # Saldo disponible en sidebar
    saldo = sesion.saldo
    st.sidebar.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0d2a26, #0d1b2a);
        border: 1px solid #1c3a36;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin-bottom: 1.2rem;
    ">
        <p style="
            font-size: 0.65rem;
            color: #26a69a;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin: 0 0 0.2rem;
        ">Saldo disponible</p>
        <p style="
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.4rem;
            font-weight: 500;
            color: #e0e6f0;
            margin: 0;
        ">${saldo:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown("---")

    # Estado del mercado
    from logic.calculos import mercado_abierto
    abierto = mercado_abierto()
    color_estado  = "#26a69a" if abierto else "#ef5350"
    texto_estado  = "MERCADO ABIERTO" if abierto else "MERCADO CERRADO"
    tiempo_estado = datetime.now(pytz.timezone("America/New_York")).strftime("%d/%m/%Y %H:%M:%S")
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
            background-color: {"#ffffff"};
            border-radius: 50%;
            display: inline-block;
            box-shadow: 0 0 6px {"#ffffff"};
        "></span>
        <span style="
            font-size: 0.68rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            color: {"#ffffff"};
        ">{tiempo_estado} Hora Nueva York</span>
    </div>
    """, unsafe_allow_html=True)


    st.sidebar.markdown("---")

    st.sidebar.markdown("""
    <div style="padding: 0.5rem 0 1.2rem;">
        <p style="
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #3a4f63;
            margin: 0 0 1rem;
        ">Horario de operación (Nueva York): 9:30 - 16:00</p>
    </div>
    """, unsafe_allow_html=True)

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
        ">Terminal Bursátil</span>
    </div>
    <p style="
        font-size: 0.75rem;
        color: #3a4f63;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin: 0 0 1rem;
    ">Simula inversiones con datos reales de mercado</p>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# PESTAÑA PORTAFOLIO
# ─────────────────────────────────────────────────────────

def _tab_portafolio(sesion, motor, db, u_id: int) -> None:

    _mostrar_portafolio(sesion, motor)

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
        with st.spinner(f"Consultando {simbolo_inv}…"):
            precio_actual = motor.obtener_precio_actual(simbolo_inv)

        if precio_actual:
            # Selector de periodo
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

            # ── Calculadora de operación ──────────────────────────────────────
            st.markdown("""
            <p style="
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: #7b8fa6;
                margin: 1.2rem 0 0.6rem;
            ">Calculadora de operación</p>
            """, unsafe_allow_html=True)

            c_val, c_cant, c_com, c_total = st.columns(4)

            with c_val:
                st.metric("Precio unitario", f"${precio_actual:,.2f}")

            with c_cant:
                cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    step=1,
                    label_visibility="visible",
                )

            monto_bruto  = precio_actual * cantidad
            comision     = calcular_comision(monto_bruto)
            total_op     = monto_bruto + comision

            with c_com:
                st.metric("Comisión (0.5%)", f"${comision:,.2f}")

            with c_total:
                st.metric("Total estimado", f"${total_op:,.2f}")

            # ── Botones de operación ──────────────────────────────────────────
            st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

            col_compra, col_venta, col_pad = st.columns([1, 1, 2])

            with col_compra:
                st.markdown("""
                <style>
                div[data-testid="stButton"]:has(button:contains("COMPRAR")) button {
                    background: linear-gradient(135deg, #0d2a26, #1a3a38) !important;
                    border: 1px solid #26a69a !important;
                    color: #26a69a !important;
                    font-weight: 600 !important;
                    letter-spacing: 0.05em !important;
                }
                div[data-testid="stButton"]:has(button:contains("COMPRAR")) button:hover {
                    background: #26a69a !important;
                    color: #060d1f !important;
                }
                </style>
                """, unsafe_allow_html=True)
                if st.button("▲ COMPRAR", width="stretch", key="btn_comprar"):
                    _ejecutar_compra(sesion, db, u_id, simbolo_inv, cantidad, precio_actual)

            with col_venta:
                st.markdown("""
                <style>
                div[data-testid="stButton"]:has(button:contains("VENDER")) button {
                    background: linear-gradient(135deg, #2a0d0d, #3a1a1a) !important;
                    border: 1px solid #ef5350 !important;
                    color: #ef5350 !important;
                    font-weight: 600 !important;
                    letter-spacing: 0.05em !important;
                }
                div[data-testid="stButton"]:has(button:contains("VENDER")) button:hover {
                    background: #ef5350 !important;
                    color: #060d1f !important;
                }
                </style>
                """, unsafe_allow_html=True)
                if st.button("▼ VENDER", width="stretch", key="btn_vender"):
                    _ejecutar_venta(sesion, db, u_id, simbolo_inv, cantidad, precio_actual)

            # Posición actual en ese ticker (si existe)
            if simbolo_inv in sesion.portafolio:
                pos = sesion.portafolio[simbolo_inv]
                valor_pos = pos["cantidad"] * precio_actual
                rend = ((precio_actual - pos["precio_compra_promedio"]) / pos["precio_compra_promedio"]) * 100
                color_rend = "#26a69a" if rend >= 0 else "#ef5350"
                signo = "▲" if rend >= 0 else "▼"

                st.markdown(f"""
                <div style="
                    background-color: #0d1b2a;
                    border: 1px solid #1c2f45;
                    border-left: 3px solid {color_rend};
                    border-radius: 0 8px 8px 0;
                    padding: 0.8rem 1.1rem;
                    margin-top: 1rem;
                    display: flex;
                    gap: 2rem;
                    flex-wrap: wrap;
                ">
                    <div>
                        <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 0.15rem">Posición actual</p>
                        <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;color:#e0e6f0;margin:0;font-weight:500">{pos['cantidad']} acciones</p>
                    </div>
                    <div>
                        <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 0.15rem">P. promedio compra</p>
                        <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;color:#e0e6f0;margin:0;font-weight:500">${pos['precio_compra_promedio']:,.2f}</p>
                    </div>
                    <div>
                        <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 0.15rem">Valor actual</p>
                        <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;color:#e0e6f0;margin:0;font-weight:500">${valor_pos:,.2f}</p>
                    </div>
                    <div>
                        <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase;margin:0 0 0.15rem">Rendimiento</p>
                        <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;color:{color_rend};margin:0;font-weight:600">{signo} {abs(rend):.2f}%</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        else:
            st.markdown(f"""
            <div style="
                background-color: #1a0d0d;
                border: 1px solid #3a1a1a;
                border-radius: 8px;
                padding: 1rem 1.2rem;
                margin-top: 0.5rem;
            ">
                <p style="color:#ef5350;font-size:0.85rem;margin:0;">
                    Ticker <strong>{simbolo_inv}</strong> no encontrado. Verifica el símbolo e intenta de nuevo.
                </p>
            </div>
            """, unsafe_allow_html=True)


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
