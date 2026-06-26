"""
frontend/app.py - TradeaYa!
Configura rutas, inicializa objetos, inyecta el sistema de diseño global
y enruta al Login o al Dashboard según el estado de sesión.

Ejecutar con:
    streamlit run src/frontend/app.py
"""

import sys
import os

import streamlit as st

# ── RUTAS ────────────────────────────────────────────────────────────────────
_SRC     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BACKEND = os.path.join(_SRC, "backend")

for _ruta in (_SRC, _BACKEND):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

# ── IMPORTACIONES ─────────────────────────────────────────────────────────────
from logic.sesion         import SesionTrading
from backend.trade_engine import TradeEngine
from backend.data_loader  import DataLoader
from backend.database     import DatabaseManager

from views.login     import mostrar_pantalla_login
from views.dashboard import mostrar_pantalla_dashboard

# ── CONFIG DE PÁGINA ──────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TradeaYa!",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── SISTEMA DE DISEÑO GLOBAL ──────────────────────────────────────────────────
# Paleta: fondo profundo #060d1f, superficie #0d1b2a, acento cian #00b4d8,
# verde compra #26a69a, rojo venta #ef5350, texto primario #e0e6f0, secundario #7b8fa6
st.markdown("""
<style>
/* ── Fuentes ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset y fondo ── */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"] {
    background-color: #060d1f !important;
    font-family: 'Inter', sans-serif !important;
    color: #e0e6f0 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #0d1b2a !important;
    border-right: 1px solid #1c2f45 !important;
}
[data-testid="stSidebar"] * {
    color: #e0e6f0 !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1c2f45 !important;
}

/* ── Header / toolbar ── */
[data-testid="stHeader"] {
    background-color: #060d1f !important;
    border-bottom: 1px solid #1c2f45 !important;
}

/* ── Bloques de contenido ── */
[data-testid="stVerticalBlock"], .block-container {
    background-color: transparent !important;
}
.block-container {
    padding-top: 3.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1280px !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] > div:first-child {
    border-bottom: 1px solid #1c2f45 !important;
    gap: 0 !important;
}
button[data-baseweb="tab"] {
    background: transparent !important;
    color: #7b8fa6 !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.4rem !important;
    border-bottom: 2px solid transparent !important;
    transition: color 0.2s, border-color 0.2s !important;
}
button[data-baseweb="tab"]:hover {
    color: #00b4d8 !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00b4d8 !important;
    border-bottom: 2px solid #00b4d8 !important;
    background: transparent !important;
}
[data-testid="stTabContent"] {
    padding-top: 1.5rem !important;
}

/* ── Métricas ── */
[data-testid="stMetric"] {
    background-color: #0d1b2a !important;
    border: 1px solid #1c2f45 !important;
    border-radius: 8px !important;
    padding: 1rem 1.2rem !important;
}
[data-testid="stMetricLabel"] {
    color: #7b8fa6 !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    color: #e0e6f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 500 !important;
}
[data-testid="stMetricDelta"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82rem !important;
}

/* ── Botones primarios (compra) ── */
[data-testid="stButton"] > button[kind="primary"],
button[kind="primary"] {
    background: linear-gradient(135deg, #26a69a, #00b4d8) !important;
    color: #060d1f !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.03em !important;
    transition: opacity 0.2s !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover {
    opacity: 0.85 !important;
}

/* ── Botones secundarios ── */
[data-testid="stButton"] > button {
    background-color: #0d1b2a !important;
    color: #e0e6f0 !important;
    border: 1px solid #1c2f45 !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    transition: border-color 0.2s, color 0.2s !important;
}
[data-testid="stButton"] > button:hover {
    border-color: #00b4d8 !important;
    color: #00b4d8 !important;
}

/* ── Botón COMPRAR (verde) ── */
button[data-testid*="comprar"], div:has(> button:contains("COMPRAR")) button {
    background-color: #1a3a38 !important;
    border-color: #26a69a !important;
    color: #26a69a !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stNumberInput"] input {
    background-color: #0d1b2a !important;
    border: 1px solid #1c2f45 !important;
    border-radius: 6px !important;
    color: #e0e6f0 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.9rem !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stNumberInput"] input:focus {
    border-color: #00b4d8 !important;
    box-shadow: 0 0 0 2px rgba(0,180,216,0.15) !important;
}
[data-testid="stTextInput"] label,
[data-testid="stNumberInput"] label {
    color: #7b8fa6 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background-color: #0d1b2a !important;
    border: 1px solid #1c2f45 !important;
    border-radius: 6px !important;
    color: #e0e6f0 !important;
}
[data-testid="stSelectbox"] label {
    color: #7b8fa6 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ── Radio buttons ── */
[data-testid="stRadio"] label {
    color: #7b8fa6 !important;
    font-size: 0.82rem !important;
}
[data-testid="stRadio"] label:has(input:checked) {
    color: #00b4d8 !important;
}
[data-testid="stRadio"] > label {
    color: #7b8fa6 !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}

/* ── DataFrames / tablas ── */
[data-testid="stDataFrame"] {
    border: 1px solid #1c2f45 !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}
[data-testid="stDataFrame"] iframe {
    border-radius: 8px !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background-color: #0d1b2a !important;
    border: 1px solid #1c2f45 !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    color: #7b8fa6 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
}
[data-testid="stExpander"] summary:hover {
    color: #00b4d8 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] {
    color: #00b4d8 !important;
}

/* ── Alertas / info / warning / error ── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    border-left-width: 3px !important;
    font-size: 0.85rem !important;
}

/* ── Dividers ── */
hr {
    border-color: #1c2f45 !important;
    margin: 1.2rem 0 !important;
}

/* ── Títulos ── */
h1, h2, h3 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    color: #e0e6f0 !important;
    letter-spacing: -0.01em !important;
}
h1 { font-size: 1.6rem !important; }
h2 { font-size: 1.2rem !important; color: #b0bec5 !important; }
h3 { font-size: 1rem !important; color: #b0bec5 !important; }

/* ── Caption / subtexto ── */
[data-testid="stCaptionContainer"], small, .stCaption {
    color: #7b8fa6 !important;
    font-size: 0.75rem !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #060d1f; }
::-webkit-scrollbar-thumb { background: #1c2f45; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #00b4d8; }

/* ── Toast ── */
[data-testid="stToast"] {
    background-color: #0d1b2a !important;
    border: 1px solid #1c2f45 !important;
    border-radius: 8px !important;
    color: #e0e6f0 !important;
}

/* ── Number input arrows ── */
[data-testid="stNumberInput"] button {
    background-color: #1c2f45 !important;
    border: none !important;
    color: #e0e6f0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── INICIALIZACIÓN DE OBJETOS ─────────────────────────────────────────────────
if "db"     not in st.session_state:
    st.session_state.db     = DatabaseManager()
if "sesion" not in st.session_state:
    st.session_state.sesion = SesionTrading()
if "motor"  not in st.session_state:
    st.session_state.motor  = TradeEngine()
if "loader" not in st.session_state:
    st.session_state.loader = DataLoader()

# ── ESTADO DE AUTENTICACIÓN ───────────────────────────────────────────────────
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id     = None
    st.session_state.usuario_nombre = None
    st.session_state.saldo_actual   = 0.0

# ── ENRUTADOR PRINCIPAL ───────────────────────────────────────────────────────
if st.session_state.usuario_id is None:
    mostrar_pantalla_login()
else:
    mostrar_pantalla_dashboard()
