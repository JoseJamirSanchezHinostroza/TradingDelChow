pip install streamlit
import streamlit as st

# Configuración básica de la página
st.set_page_config(page_title="TradeaYa! - Simulador", page_icon="📈", layout="wide")

# Título principal
st.title("📈 TradeaYa! - Plataforma de Trading")
st.markdown("---")

# Crear columnas para dividir la pantalla (Izquierda: Operaciones, Derecha: Dashboard)
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🛒 Panel de Operaciones")
    # Cajas de texto para que el usuario escriba
    simbolo = st.text_input("Símbolo de la acción (Ej. AAPL, TSLA):")
    cantidad = st.number_input("Cantidad a operar:", min_value=1, step=1)
    
    # Botones en fila
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🟩 COMPRAR", use_container_width=True):
            st.info(f"Hiciste clic en Comprar {cantidad} de {simbolo}. (Lógica pendiente)")
    
    with btn_col2:
        if st.button("🟥 VENDER", use_container_width=True):
            st.info(f"Hiciste clic en Vender {cantidad} de {simbolo}. (Lógica pendiente)")

with col2:
    st.subheader("📊 Dashboard Principal")
    # Tarjetas de resumen simuladas (luego las conectaremos a tu sesion.get_resumen())
    metric_col1, metric_col2, metric_col3 = st.columns(3)
    metric_col1.metric("Saldo Disponible", "$100,000.00")
    metric_col2.metric("Valor del Portafolio", "$0.00")
    metric_col3.metric("Patrimonio Total", "$100,000.00")
    
    st.markdown("---")
    st.subheader("💼 Tus Posiciones")
    st.write("Aún no tienes acciones en tu portafolio.")

st.markdown("---")
st.subheader("📝 Historial de Transacciones")
st.write("Aquí aparecerá el registro de todas tus compras y ventas.")
