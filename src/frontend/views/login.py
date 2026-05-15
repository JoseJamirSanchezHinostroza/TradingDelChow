"""
frontend/views/login.py - TradeaYa!
Pantalla de inicio de sesión y registro de nuevos usuarios.
"""

import time
import streamlit as st


def mostrar_pantalla_login() -> None:
    st.title("🔐 Bienvenido a TradeaYa!")
    st.subheader("Inicia sesión para acceder a tu terminal de inversión")

    db = st.session_state.db

    tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Registrarse"])

    # ── Iniciar sesión ────────────────────────────────────────────────────────
    with tab_login:
        email    = st.text_input("Correo electrónico", key="login_email")
        password = st.text_input("Contraseña", type="password", key="login_pass")

        if st.button("Ingresar", type="primary"):
            usuario = db.verificar_login(email, password)
            if usuario:
                st.session_state.usuario_id     = usuario[0]
                st.session_state.usuario_nombre = usuario[1]
                st.session_state.saldo_actual   = usuario[2]
                st.success(f"¡Bienvenido de vuelta, {usuario[1]}!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Credenciales incorrectas. Intenta de nuevo.")

    # ── Registro ──────────────────────────────────────────────────────────────
    with tab_registro:
        nombre   = st.text_input("Nombre completo",       key="reg_nombre")
        email_r  = st.text_input("Correo electrónico",    key="reg_email")
        password_r = st.text_input("Contraseña", type="password", key="reg_pass")

        if st.button("Crear Cuenta", type="primary"):
            if nombre and email_r and password_r:
                exito, mensaje = db.registrar_usuario(nombre, email_r, password_r)
                if exito:
                    st.success("¡Cuenta creada! Ve a 'Iniciar Sesión' para entrar.")
                else:
                    st.error(mensaje)
            else:
                st.warning("Por favor, completa todos los campos.")
