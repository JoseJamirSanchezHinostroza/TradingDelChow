import streamlit as st
import time
import sys
import os

# Truco para que Streamlit encuentre tu carpeta 'logic' sin errores de rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from logic.sesion import SesionTrading

# Configuración básica de la página
st.set_page_config(page_title="TradeaYa! - Simulador", page_icon="📈", layout="wide")

# --- 1. MEMORIA DE LA APLICACIÓN (Session State) ---
if 'sesion_trading' not in st.session_state:
    st.session_state.sesion_trading = SesionTrading()

sesion = st.session_state.sesion_trading

# --- 2. PRECIOS FALSOS (Hasta que tu compañero de Backend termine) ---
# Usamos un precio por defecto de $100.00 para cualquier acción que no esté aquí
precios_actuales = {"AAPL": 150.00, "TSLA": 200.00, "AMZN": 130.00}

st.title("📈 TradeaYa! - Plataforma de Trading")
st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🛒 Panel de Operaciones")
    simbolo = st.text_input("Símbolo de la acción (Ej. AAPL, TSLA):").upper()
    cantidad = st.number_input("Cantidad a operar:", min_value=1, step=1)
    
    # Obtenemos el precio falso para simular la operación
    precio_simulado = precios_actuales.get(simbolo, 100.00) 
    
    st.write(f"Precio actual en mercado: **${precio_simulado:.2f}**")

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🟩 COMPRAR", use_container_width=True):
            if no simbolo:
                st.warning("Escribe un símbolo primero.")
            else:
                # LLAMAMOS A TU LÓGICA
                exito, mensaje = sesion.comprar(simbolo, cantidad, precio_simulado, time.time())
                if exito:
                    st.success(mensaje)
                else:
                    st.error(mensaje)
    
    with btn_col2:
        if st.button("🟥 VENDER", use_container_width=True):
            if no simbolo:
                st.warning("Escribe un símbolo primero.")
            else:
                # LLAMAMOS A TU LÓGICA
                exito, mensaje = sesion.vender(simbolo, cantidad, precio_simulado, time.time())
                if exito:
                    st.success(mensaje)
                else:
                    st.error(mensaje)

with col2:
    st.subheader("📊 Dashboard Principal")
    
    # LLAMAMOS A TU RESUMEN PARA ACTUALIZAR LOS NÚMEROS
    resumen = sesion.get_resumen(precios_actuales)
    
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Saldo Disponible", f"${resumen['saldo_disponible']:,.2f}")
    metric_col2.metric("Valor del Portafolio", f"${resumen['valor_portafolio']:,.2f}")
    metric_col3.metric("Patrimonio Total", f"${resumen['patrimonio_total']:,.2f}")
    
    st.markdown("---")
    st.subheader("💼 Tus Posiciones")
    
    # Mostrar la tabla de posiciones si hay acciones
    if resumen['posiciones']:
        st.table(resumen['posiciones'])
    else:
        st.info("Aún no tienes acciones en tu portafolio.")

st.markdown("---")
st.subheader("📝 Historial de Transacciones (Próximamente)")
st.write("Aquí conectaremos el registro de tus operaciones más adelante.")
