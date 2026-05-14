import streamlit as st
import time

def mostrar_pantalla_login():
    st.title("🔐 Bienvenido a TradeaYa!")
    st.subheader("Inicia sesión para acceder a tu terminal de inversión")
    
    # Traemos la base de datos de la memoria
    db = st.session_state.db
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registrarse"])
    
    with tab1:
        email_login = st.text_input("Correo electrónico")
        pass_login = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar", type="primary"):
            usuario = db.verificar_login(email_login, pass_login)
            if usuario:
                # Guardamos los datos del usuario en la sesión para que no se borren
                st.session_state.usuario_id = usuario[0]
                st.session_state.usuario_nombre = usuario[1]
                st.session_state.saldo_actual = usuario[2]
                st.success(f"¡Bienvenido de vuelta, {usuario[1]}!")
                time.sleep(1)
                st.rerun() # Recarga la app para pasar al dashboard
            else:
                st.error("Credenciales incorrectas. Intenta de nuevo.")

    with tab2:
        nombre_reg = st.text_input("Nombre completo")
        email_reg = st.text_input("Nuevo correo electrónico")
        pass_reg = st.text_input("Nueva contraseña", type="password")
        
        if st.button("Crear Cuenta", type="primary"):
            if nombre_reg and email_reg and pass_reg:
                db.registrar_usuario(nombre_reg, email_reg, pass_reg)
                st.success("¡Cuenta creada con éxito! Ve a 'Iniciar Sesión' para entrar.")
            else:
                st.warning("Por favor, llena todos los campos.")