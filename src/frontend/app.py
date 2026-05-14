import streamlit as st
import time
import sys
import os
import pandas as pd

# --- TRUCO DE RUTAS ---
ruta_src = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(ruta_src)

ruta_backend = os.path.abspath(os.path.join(ruta_src, 'backend'))
sys.path.append(ruta_backend)

# --- IMPORTACIONES DEL BACKEND (Respetando la arquitectura) ---
from logic.sesion import SesionTrading
from backend.trade_engine import TradeEngine
from backend.data_loader import DataLoader

# Configuración estética
st.set_page_config(page_title="TradeaYa! - Pro", page_icon="📈", layout="wide")

# Inicializamos las herramientas conectadas a la Base de Datos y Backend
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
    # Agregamos .strip() para borrar espacios invisibles que rompen el DataLoader
    simbolo = st.text_input("Ingrese Ticker (ej: AAPL, TSLA, NVDA):").strip().upper()
    cantidad = st.number_input("Cantidad:", min_value=1, step=1)
    
    precio_actual = 0.0

    if simbolo:
        with st.spinner(f'Consultando mercado por {simbolo}...'):
            precio_actual = motor.obtener_precio_actual(simbolo)
            
            if precio_actual:
                st.metric(label=f"Precio Actual {simbolo}", value=f"${precio_actual:,.2f}")
                
                # --- GRÁFICO (USANDO EL DATALOADER DEL BACKEND) ---
                st.markdown(f"### 📈 Análisis de Tendencia: {simbolo}")
                
                try:
                    # Llamamos a la función oficial de tu compañero
                    datos_hist = loader.obtener_datos_grafico(simbolo, periodo="1mo")
                    
                    if datos_hist:
                        # Convertimos el diccionario del DataLoader a gráfico
                        serie_precios = pd.Series(datos_hist)
                        serie_precios.index = pd.to_datetime(serie_precios.index).date
                        
                        st.area_chart(serie_precios, color="#29b5e8")
                        
                        inicio = serie_precios.iloc[0]
                        fin = serie_precios.iloc[-1]
                        variacion = ((fin - inicio) / inicio) * 100
                        st.caption(f"Variación del último mes: **{variacion:+.2f}%**")
                    else:
                        st.warning(f"⚠️ El DataLoader del backend no encontró historial para {simbolo}.")
                except Exception as e:
                    st.error(f"Error procesando los datos del backend: {e}")
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
    
    precios_vivos = {}
    for s in sesion.portafolio.keys():
        p = motor.obtener_precio_actual(s)
        if p: precios_vivos[s] = p
    
    resumen = sesion.get_resumen(precios_vivos)
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Saldo Disponible", f"${resumen['saldo_disponible']:,.2f}")
    k2.metric("Valor Acciones", f"${resumen['valor_portafolio']:,.2f}")
    k3.metric("Patrimonio Total", f"${resumen['patrimonio_total']:,.2f}")

    st.markdown("---")
    if resumen['posiciones']:
        st.write("### Posiciones Abiertas")
        df_p = pd.DataFrame(resumen['posiciones'])
        st.dataframe(df_p.style.format({
            'precio_compra': '${:.2f}', 
            'precio_actual': '${:.2f}',
            'rendimiento_%': '{:.2f}%'
        }), use_container_width=True)
    else:
        st.info("Tu portafolio está vacío. ¡Empieza a tradear!")