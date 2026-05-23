"""
frontend/app.py - TradeaYa!
Aquí Streamlit reproduce la página web. Configura rutas para importaciones,
inicializa objetos y enruta al Login o al Dashboard según el estado de sesión.

Este es el archivo a ejecutar mediante el siguiente comando en la terminal:
    streamlit run src/frontend/app.py
"""

import sys # Interacción directa con el intérprete y SO
import os # Interacción directa con el SO

import streamlit as st # Motor gráfico de la página

# ── RUTAS: Agrega src/ y src/backend/ al path para que las importaciones funcionen sin instalar el proyecto como paquete ──────
_SRC     = os.path.abspath(os.path.join(os.path.dirname(__file__), "..")) # Utiliza os para encontrar la ruta exacta de src
_BACKEND = os.path.join(_SRC, "backend") # Construye la ruta hacia la carpeta del BackEnd

for _ruta in (_SRC, _BACKEND):
    if _ruta not in sys.path:
        sys.path.insert(0, _ruta) # Inserta a la memoria de Python ambas carpetas si no están mediante iteración.

# ── IMPORTACIONES: Python sabe que buscar gracias a RUTAS────────────────────────────────────────────────────────────
from logic.sesion       import SesionTrading # Control de lógica
from backend.trade_engine import TradeEngine # Conexión a Yahoo Finance y Alpaca para precios
from backend.data_loader  import DataLoader # Genración de reportes del historial de transacciones
from backend.database     import DatabaseManager # Conexión y operaciones sobre la DB

from views.login     import mostrar_pantalla_login # Pantalla de loggeo/registro
from views.dashboard import mostrar_pantalla_dashboard # Pantalla dónde el usuario opera

# ── CONFIG DE PÁGINA ──────────────────────────────────────────────────
st.set_page_config(page_title="TradeaYa!", page_icon="📈", layout="wide") # Define nombre de la página y la ocupación total de la pantalla

# ── INICIALIZACIÓN DE OBJETOS (evento único por sesión) ────────────────────────────
""" Si algo no se encuentra en la memoria de sesión, lo crea utilizando las clases importadas: los datos sobreviven los refresh """
if "db"     not in st.session_state:
    st.session_state.db     = DatabaseManager()
if "sesion" not in st.session_state:
    st.session_state.sesion = SesionTrading()
if "motor"  not in st.session_state:
    st.session_state.motor  = TradeEngine()
if "loader" not in st.session_state:
    st.session_state.loader = DataLoader()

# ── ESTADO DE AUTENTICACIÓN (evento único por sesión) ────────────────────────
"""Si el ID de usuario no se encuentra en la memoria de sesión, inicializa variables por seguridad"""
if "usuario_id" not in st.session_state:
    st.session_state.usuario_id     = None
    st.session_state.usuario_nombre = None
    st.session_state.saldo_actual   = 0.0

# ── ENRUTADOR PRINCIPAL ───────────────────────────────────────────────────────
""" Si el ID de usuario se encuentra en la memoria de sesión, vas directo a la pantalla de operaciones (DashBoard). Si no, te manda a iniciar sesión (funciones de views)"""
if st.session_state.usuario_id is None:
    mostrar_pantalla_login()
else:
    mostrar_pantalla_dashboard()
