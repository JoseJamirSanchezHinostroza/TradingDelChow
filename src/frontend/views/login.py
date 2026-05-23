"""
frontend/views/login.py - TradeaYa!
Pantalla de inicio de sesión y registro de nuevos usuarios.
"""

import time # Librería tiempo
import streamlit as st # Streamlit como motor gráfico de la página web


def mostrar_pantalla_login() -> None:
    st.title("🔐 Bienvenido a TradeaYa!")
    st.subheader("Inicia sesión para acceder a tu terminal de inversión")

    db = st.session_state.db # Extrae la conexión de la memoria de sesión a la DB .

    tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Registrarse"]) # Genera 2 pestañas navegables distintas con tabs: Inicio de sesión o registro

    # ── PESTAÑA 1: INICIO DE SESIÓN ────────────────────────────────────────────────────────
    with tab_login:
        """ Caja de texto para ingresar el correo (key porque hay 1 caja email en cada tab, evita la confusión del programa) y contraseña (type para ocultar lo escrito) """
        email    = st.text_input("Correo electrónico", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_pass")

        if st.button("Ingresar", type="primary"): # Si se presiona el botón Ingresar
            usuario = db.verificar_login(email, password) # Se revisa si hay un match con un par email-password de la DataBase (tabla usuarios)
            if usuario: # Devolvió match (credenciales correctas)
                st.session_state.usuario_id     = usuario[0] # Guarda en la memoria de sesión el ID del usuario
                st.session_state.usuario_nombre = usuario[1] # // el nombre del usuario
                st.session_state.saldo_actual   = usuario[2] # // el saldo actual del usuario
                st.success(f"¡Bienvenido de vuelta, {usuario[1]}!") # Bienvenida al usuario
                time.sleep(1) # Congelación para visualizar el mensaje
                st.rerun() # Refresco para actualización
            else:
                st.error("Credenciales incorrectas. Intenta de nuevo.") # Cuadro rojo de Error

    # ── PESTAÑA 2: REGISTRO ──────────────────────────────────────────────────────────────
    with tab_registro:
        """ Creación de 3 campos para registro (Nombre-Email-Contraseña). Utiliza key para evitar confusión con la otra tab. """
        nombre   = st.text_input("Nombre completo",       key="reg_nombre")
        email_r  = st.text_input("Correo electrónico",    key="reg_email")
        password_r = st.text_input("Contraseña", type="password", key="reg_pass")

        if st.button("Crear Cuenta", type="primary"): # Si se presiona el botón Crear Cuenta
            if nombre and email_r and password_r: # No hay vacíos en ningún campo
                exito, mensaje = db.registrar_usuario(nombre, email_r, password_r) # Intento de insertación de la nueva fila a la DataBase
                if exito:
                    st.success("¡Cuenta creada! Ve a 'Iniciar Sesión' para entrar.") # Registro completo, DB devolvió True. Te invita a iniciar sesión.
                else:
                    st.error(mensaje) # Error (correo ya usado), muestra mensaje de error de la DB, que devolvió False
            else:
                st.warning("Por favor, completa todos los campos.") # Se dejó un campo en blanco
