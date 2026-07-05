"""
frontend/views/login.py - TradeaYa!
Pantalla de inicio de sesión y registro de nuevos usuarios.
"""

import re
import time
import streamlit as st



# ── Validación de email ───────────────────────────────────────────────────────
_RE_EMAIL = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

def _email_valido(email: str) -> bool:
    """Devuelve True si el email tiene formato válido (RFC 5322 simplificado)."""
    return bool(_RE_EMAIL.match(email.strip()))


def mostrar_pantalla_login() -> None:

    db = st.session_state.db

    # ── Hero header ──────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        text-align: center;
        padding: 3rem 1rem 2rem;
    ">
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.5rem;
        ">
            <span style="font-size: 2rem;">📈</span>
            <span style="
                font-family: 'Inter', sans-serif;
                font-size: 2rem;
                font-weight: 700;
                color: #e0e6f0;
                letter-spacing: -0.02em;
            ">TradeaYa!</span>
        </div>
        <p style="
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            color: #7b8fa6;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin: 0;
        ">Terminal de inversión simulada · Mercados reales</p>
        <div style="
            width: 40px;
            height: 2px;
            background: linear-gradient(90deg, #26a69a, #00b4d8);
            margin: 1rem auto 0;
            border-radius: 2px;
        "></div>
    </div>
    """, unsafe_allow_html=True)

    # ── Panel central ─────────────────────────────────────────────────────────
    _, col_form, _ = st.columns([1, 1.2, 1])

    with col_form:
        st.markdown("""
        <div style="
            background-color: #0d1b2a;
            border: 1px solid #1c2f45;
            border-radius: 12px;
            padding: 2rem 2rem 1.5rem;
        ">
        """, unsafe_allow_html=True)

        tab_login, tab_registro = st.tabs(["Iniciar sesión", "Crear cuenta"])

        # ── TAB LOGIN ────────────────────────────────────────────────────────
        with tab_login:
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            email    = st.text_input("Correo electrónico", key="login_email", placeholder="tu@correo.com")
            password = st.text_input("Contraseña", type="password", key="login_pass", placeholder="••••••••")
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

            if st.button("Ingresar", type="primary", use_container_width=True):
                if not email or not password:
                    st.warning("Completa ambos campos.")
                else:
                    usuario = db.verificar_login(email, password)
                    if usuario:
                        st.session_state.usuario_id     = usuario[0]
                        st.session_state.usuario_nombre = usuario[1]
                        st.session_state.saldo_actual   = usuario[2]
                        # Persistir uid en query_params para sobrevivir reruns de Cloud
                        st.query_params["uid"] = str(usuario[0])
                        st.success(f"Bienvenido de vuelta, {usuario[1]}.")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas. Intente de nuevo")

        # ── TAB REGISTRO ─────────────────────────────────────────────────────
        with tab_registro:
            st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
            nombre     = st.text_input("Nombre completo",    key="reg_nombre",  placeholder="Ana García")
            email_r    = st.text_input("Correo electrónico", key="reg_email",   placeholder="tu@correo.com")
            password_r = st.text_input("Contraseña",         key="reg_pass",    placeholder="Mín. 6 caracteres", type="password")
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

            if st.button("Crear cuenta", type="primary", use_container_width=True):
                if not all([nombre, email_r, password_r]):
                    st.warning("Completa todos los campos.")
                elif not _email_valido(email_r):
                    st.warning("Ingrese un correo electrónico válido.")
                elif len(password_r) < 6:
                    st.warning("La contraseña debe tener al menos 6 caracteres.")
                else:
                    exito, mensaje = db.registrar_usuario(nombre, email_r, password_r)
                    if exito:
                        st.success("Cuenta creada exitosamente.")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error(mensaje)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="
        text-align: center;
        margin-top: 2.5rem;
        padding-bottom: 1rem;
    ">
        <p style="
            font-family: 'Inter', sans-serif;
            font-size: 0.72rem;
            color: #3a4f63;
            letter-spacing: 0.05em;
        ">
            EXCLUSIVAMENTE PARA FINES EDUCATIVOS · MERCADO REAL - DINERO FICTICIO · NO SE REALIZAN TRANSACCIONES REALES
        </p>
    </div>
    """, unsafe_allow_html=True)
