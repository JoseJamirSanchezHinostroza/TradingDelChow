"""
frontend/views/helpers/sidebar.py - TradeaYa!
Barra lateral del Terminal de inversión: Uusuario, Saldo, Horarios y Cierre de Sesión.
"""
from datetime import datetime
import pytz
import time
import streamlit as st

from logic.calculos import mercado_abierto

# 1. CREAMOS EL FRAGMENTO AISLADO PARA EL RELOJ Y ESTADO
@st.fragment(run_every=1)
def _reloj_mercado_en_vivo() -> None:
    """Este bloque se actualiza automáticamente cada 1 segundo sin recargar toda la app."""
    abierto = mercado_abierto()
    color_estado  = "#26a69a" if abierto else "#ef5350"
    texto_estado  = "MERCADO ABIERTO" if abierto else "MERCADO CERRADO"
    tiempo_estado = datetime.now(pytz.timezone("America/New_York")).strftime("%d/%m/%Y %H:%M:%S")
    
    # Renderizamos los mismos divs que elegiste, pero usando st.markdown genérico 
    # (se ubicarán en el sidebar gracias al bloque 'with st.sidebar' más abajo)
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.6rem 0;
        margin-bottom: 0.5rem;
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


# 2. TU FUNCIÓN PRINCIPAL DEL SIDEBAR
def _renderizar_sidebar(sesion, motor, u_id: int) -> None:
    """Sidebar: perfil del usuario y saldo en tiempo real."""

    st.sidebar.markdown("""
    <div style="padding: 0.5rem 0 1rem;">
        <p style="
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #3a4f63;
            margin: 0 rem;
        ">CUENTA ACTIVA</p>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.markdown(f"""
    <div style="
        background-color: #060d1f;
        border: 1px solid #1c2f45;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    ">
        <p style="
            font-size: 0.68rem;
            color: #3a4f63;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0 0 0.1rem;
        ">Usuario</p>
        <p style="
            font-size: 1rem;
            font-weight: 600;
            color: #e0e6f0;
            margin: 0 0 0.4rem;
        ">{st.session_state.usuario_nombre}</p>
        <p style="
            font-size: 0.68rem;
            color: #3a4f63;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0 0 0.1rem;
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
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
    ">
        <p style="
            font-size: 0.65rem;
            color: #26a69a;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin: 0 0 0.1rem;
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

    # 3. LLAMAMOS AL FRAGMENTO EN VIVO
    # Usamos 'with st.sidebar' para que el fragmento se dibuje aquí adentro
    with st.sidebar:
        _reloj_mercado_en_vivo()

    st.sidebar.markdown("---")

    st.sidebar.markdown("""
    <div style="padding: 0.2rem 0 0.8rem;">
        <p style="
            font-size: 0.65rem;
            font-weight: 600;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #3a4f63;
            margin: 0;
        ">Horario de operación (Nueva York): 9:30 - 16:00</p>
    </div>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Cerrar sesión", width="stretch"):
        st.session_state.usuario_id = None
        st.session_state.pop("db_sincronizada", None)
        # Limpiar uid de query_params para que no se restaure la sesión
        st.query_params.clear()
        st.rerun()

