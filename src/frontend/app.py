import streamlit as st
import sys
import os

# --- TRUCO DE RUTAS (Debe ir antes de las importaciones) ---
ruta_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ruta_src not in sys.path: sys.path.append(ruta_src)

ruta_backend = os.path.abspath(os.path.join(ruta_src, 'backend'))
if ruta_backend not in sys.path: sys.path.append(ruta_backend)

# --- IMPORTACIONES ---
from logic.sesion import SesionTrading
from backend.trade_engine import TradeEngine
from backend.data_loader import DataLoader
from backend.database import DatabaseManager

# Importamos las Vistas Modulares
from views.login import mostrar_pantalla_login
from views.dashboard import mostrar_pantalla_dashboard

# Configuración estética
st.set_page_config(page_title="TradeaYa! - Pro", page_icon="📈", layout="wide")

# --- 1. INICIALIZAR MEMORIA Y BASE DE DATOS ---
if 'db' not in st.session_state:
    st.session_state.db = DatabaseManager()
if 'sesion' not in st.session_state:
    st.session_state.sesion = SesionTrading()
if 'motor' not in st.session_state:
    st.session_state.motor = TradeEngine()
if 'loader' not in st.session_state:
    st.session_state.loader = DataLoader()

# --- 2. CONTROL DE SESIÓN ---
if 'usuario_id' not in st.session_state:
    st.session_state.usuario_id = None
    st.session_state.usuario_nombre = None
    st.session_state.saldo_actual = 0.0

# --- 3. ENRUTADOR PRINCIPAL ---
# Si no hay nadie logueado, dibuja el Login. Si lo hay, dibuja el Dashboard.
if st.session_state.usuario_id is None:
    mostrar_pantalla_login()
else:
    mostrar_pantalla_dashboard()