import streamlit as st
import time
import sys
import os
import pandas as pd

# Configuración de rutas para que reconozca 'logic' y 'backend'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from logic.sesion import SesionTrading
from backend.trade_engine import TradeEngine
from backend.data_loader import DataLoader

# Configuración estética de la página
st.set_page_config(page_title="TradeaYa! - Pro", page_icon="📈", layout="wide")

# Inicializamos las herramientas en el estado de la sesión
if 'sesion' not in st.session_state:
    st.session_state.sesion = SesionTrading()
if 'motor' not in st.session_state:
    st.session_state.motor = TradeEngine()
if 'loader' not in st.session_state:
    st.session_state.loader = DataLoader()

sesion = st.session_state.sesion
motor = st.session_state.motor
loader = st.session_state.loader

st.title("📈 TradeaYa! | Terminal de Inversión")
st.markdown("---")

col_izq, col_der = st.columns([1, 2])

with col_izq:
    st.subheader("⚡ Operaciones")
    simbolo = st.text_input("Ingrese Ticker (ej: AAPL, TSLA, NVDA):").upper()
    cantidad = st.number_input("Cantidad:", min_value=1, step=1)
    
    precio_actual = 0.0

    if simbolo:
        with st.spinner(f'Consultando mercado por {simbolo}...'):
            # 1. Validamos y obtenemos el precio REAL del motor de tu compañero
            precio_actual = motor.obtener_precio_actual(simbolo)
            
            if precio_actual:
                st.metric(label=f"Precio Actual {simbolo}", value=f"${precio_actual:,.2f}")
                
                # 2. GRÁFICO CHULO: Usamos el DataLoader para el historial
                st.markdown(f"**Historial del último mes:**")
                datos_hist = loader.obtener_datos_grafico(simbolo)
                if datos_hist:
                    # Convertimos el diccionario a un DataFrame para que Streamlit lo entienda bien
                    df_hist = pd.DataFrame.from_dict(datos_hist, orient='index', columns=['Precio'])
                    # st.area_chart se ve mucho más "cool" (rellena el fondo)
                    st.area_chart(df_hist, color="#29b5e8")
                else:
                    st.warning("No se encontraron datos históricos.")
            else:
                st.error("Símbolo no encontrado o error de conexión.")

    # Botonera
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🟩 COMPRAR", use_container_width=True):
            if precio_actual > 0:
                exito, msg = sesion.comprar(simbolo, cantidad, precio_actual, time.time())
                if exito: st.success(msg)
                else: st.error(msg)
    with c2:
        if st.button("🟥 VENDER", use_container_width=True):
            if precio_actual > 0:
                exito, msg = sesion.vender(simbolo, cantidad, precio_actual, time.time())
                if exito: st.success(msg)
                else: st.error(msg)

with col_der:
    st.subheader("📊 Mi Portafolio Real")
    
    # Actualizamos los precios de todas las acciones que el usuario posee
    precios_vivos = {}
    for s in sesion.portafolio.keys():
        p = motor.obtener_precio_actual(s)
        if p: precios_vivos[s] = p
    
    resumen = sesion.get_resumen(precios_vivos)
    
    # KPIs Superiores
    k1, k2, k3 = st.columns(3)
    k1.metric("Saldo Disponible", f"${resumen['saldo_disponible']:,.2f}")
    k2.metric("Valor Acciones", f"${resumen['valor_portafolio']:,.2f}")
    k3.metric("Patrimonio Total", f"${resumen['patrimonio_total']:,.2f}", 
              delta=f"{((resumen['patrimonio_total']/100000)-1)*100:.2f}%")

    st.markdown("---")
    if resumen['posiciones']:
        st.write("### Posiciones Abiertas")
        df_p = pd.DataFrame(resumen['posiciones'])
        # Formateamos para que se vea estético
        st.dataframe(df_p.style.format({
            'precio_compra': '${:.2f}', 
            'precio_actual': '${:.2f}',
            'rendimiento_%': '{:.2f}%'
        }), use_container_width=True)
    else:
        st.info("Tu portafolio está vacío. ¡Empieza a tradear!")