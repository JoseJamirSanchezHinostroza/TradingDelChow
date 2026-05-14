import streamlit as st
import time
import pandas as pd

def mostrar_pantalla_dashboard():
    # Recuperamos las herramientas de la sesión
    sesion = st.session_state.sesion
    motor = st.session_state.motor
    loader = st.session_state.loader

    # --- BARRA LATERAL (PERFIL) ---
    st.sidebar.title("Mi Perfil")
    st.sidebar.write(f"👤 **{st.session_state.usuario_nombre}**")
    st.sidebar.write(f"💼 ID Cuenta: #{st.session_state.usuario_id}")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.usuario_id = None
        st.rerun() # Esto nos devolverá al Login

    # --- PANTALLA PRINCIPAL ---
    st.title("📈 TradeaYa! | Terminal de Inversión")
    st.markdown("---")

    col_izq, col_der = st.columns([1, 2])

    with col_izq:
        st.subheader("⚡ Operaciones")
        simbolo = st.text_input("Ingrese Ticker (ej: AAPL, TSLA, NVDA):").strip().upper()
        cantidad = st.number_input("Cantidad:", min_value=1, step=1)
        
        precio_actual = 0.0

        if simbolo:
            with st.spinner(f'Consultando mercado por {simbolo}...'):
                precio_actual = motor.obtener_precio_actual(simbolo)
                
                if precio_actual:
                    st.metric(label=f"Precio Actual {simbolo}", value=f"${precio_actual:,.2f}")
                    st.markdown(f"### 📈 Análisis de Tendencia: {simbolo}")
                    
                    try:
                        datos_hist = loader.obtener_datos_grafico(simbolo, periodo="1mo")
                        if datos_hist:
                            serie_precios = pd.Series(datos_hist)
                            serie_precios.index = pd.to_datetime(serie_precios.index).date
                            st.area_chart(serie_precios, color="#29b5e8")
                            
                            inicio = serie_precios.iloc[0]
                            fin = serie_precios.iloc[-1]
                            variacion = ((fin - inicio) / inicio) * 100
                            st.caption(f"Variación del último mes: **{variacion:+.2f}%**")
                        else:
                            st.warning(f"⚠️ El DataLoader no encontró historial para {simbolo}.")
                    except Exception as e:
                        st.error(f"Error procesando datos: {e}")
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