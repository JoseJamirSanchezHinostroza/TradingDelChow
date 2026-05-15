"""
frontend/app.py - TradeaYa!
Punto de entrada de Streamlit. Configura rutas, inicializa objetos
y enruta al Login o al Dashboard según el estado de sesión.

Ejecutar desde la raíz del proyecto con:
    streamlit run src/frontend/app.py
"""

import sys
import os

import streamlit as st

# ── Rutas ────────────────────────────────────────────────────────────────────
# Agrega src/ y src/backend/ al path para que las importaciones funcionen
# sin instalar el proyecto como paquete.
_SRC     = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_BACKEND = os.path.join(_SRC, "backend")

for _ruta in (_SRC, _BACKEND):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta)

# ── Importaciones ────────────────────────────────────────────────────────────
from logic.sesion       import SesionTrading
from backend.trade_engine import TradeEngine
from backend.data_loader  import DataLoader
from backend.database     import DatabaseManager

from views.login     import mostrar_pantalla_login
from views.dashboard import mostrar_pantalla_dashboard

# ── Configuración de página ──────────────────────────────────────────────────
st.set_page_config(page_title="TradeaYa!", page_icon="📈", layout="wide")

# ── Inicializar objetos (una sola vez por sesión) ────────────────────────────
if "db"     not in st.session_state:
    st.session_state.db     = DatabaseManager()
if "sesion" not in st.session_state:
    st.session_state.sesion = SesionTrading()
if "motor"  not in st.session_state:
    st.session_state.motor  = TradeEngine()
if "loader" not in st.session_state:
    st.session_state.loader = DataLoader()

# ── Estado de autenticación (una sola vez por sesión) ────────────────────────
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id     = None
    st.session_state.usuario_nombre = None
    st.session_state.saldo_actual   = 0.0

# ── Enrutador principal ───────────────────────────────────────────────────────
if st.session_state.usuario_id is None:
    mostrar_pantalla_login()
else:
    mostrar_pantalla_dashboard()
