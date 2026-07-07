"""
frontend/views/helpers/precio_live.py - TradeaYa!
Fragmentos de precio en tiempo real usando st.fragment(run_every=60).
Cada fragmento se re-ejecuta cada 60 s de forma independiente,
sin rerenderizar el resto de la app.

Expone tres fragmentos invocables:
  - precio_portafolio_live(sesion, motor)        → métricas y tabla de posiciones
  - precio_ticker_live(motor, simbolo, sesion)   → precio + calculadora en Zona de Inversión
  - precio_sidebar_live(sesion)                  → saldo en sidebar
"""

import time
import pandas as pd
import streamlit as st

from logic.calculos import calcular_comision
from views.helpers.auxiliares import _ejecutar_compra, _ejecutar_venta


# ─────────────────────────────────────────────────────────
# FRAGMENTO 1: Métricas + tabla de posiciones (Portafolio)
# ─────────────────────────────────────────────────────────

@st.fragment(run_every=60)
def precio_portafolio_live(sesion, motor) -> None:
    """
    Se refresca cada 60 s. Muestra métricas de cuenta y tabla de posiciones
    con precios actualizados desde el backend.
    """
    precios_vivos = {
        s: p
        for s in sesion.portafolio
        if (p := motor.obtener_precio_actual(s)) is not None
    }

    resumen   = sesion.get_resumen(precios_vivos)
    costo_inv = sum(p["cantidad"] * p["precio_compra"] for p in resumen["posiciones"])
    ganancia  = resumen["valor_portafolio"] - costo_inv
    retorno   = resumen["patrimonio_total"] - 10_000.00

    # Guardar precios en session_state para que el resto de la pestaña los use
    st.session_state["_precios_vivos"]  = precios_vivos
    st.session_state["_resumen_cache"]  = resumen

    # ── Métricas ──────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Saldo disponible",    f"${resumen['saldo_disponible']:,.2f}")
    k2.metric("Valor del portafolio", f"${resumen['valor_portafolio']:,.2f}",
              delta=f"${ganancia:,.2f}" if costo_inv > 0 else None)
    k3.metric("Patrimonio total",    f"${resumen['patrimonio_total']:,.2f}",
              delta=f"${retorno:,.2f}")
    k4.metric("Operaciones realizadas", resumen["total_operaciones"])

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Tabla de posiciones ───────────────────────────────
    if resumen["posiciones"]:
        st.markdown("""
        <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;
                  text-transform:uppercase;color:#7b8fa6;margin-bottom:0.5rem;">
        Posiciones abiertas</p>
        """, unsafe_allow_html=True)

        df = pd.DataFrame(resumen["posiciones"])
        df = df.rename(columns={
            "simbolo"      : "Símbolo",
            "cantidad"     : "Cant.",
            "precio_compra": "P. Compra",
            "precio_actual": "P. Actual",
            "rendimiento_%" : "Rend. %",
        })
        df.index = range(1, len(df) + 1)

        fmt_precio = lambda v: f"${v:,.2f}" if v is not None else "N/A"
        fmt_rend   = lambda v: f"{v:+.2f}%" if v is not None else "N/A"

        st.dataframe(
            df.style.format({
                "P. Compra": fmt_precio,
                "P. Actual": fmt_precio,
                "Rend. %"  : fmt_rend,
            }).map(
                lambda v: "color: #26a69a" if isinstance(v, str) and v.startswith("+")
                     else ("color: #ef5350" if isinstance(v, str) and v.startswith("-") else ""),
                subset=["Rend. %"],
            ),
            width="stretch",
            height=min(80 + len(df) * 38, 400),
        )

        # Timestamp de última actualización
        st.caption(f"⟳ Precio actualizado: {time.strftime('%H:%M:%S')}  ·  próximo refresco en 60 s")
    else:
        st.markdown("""
        <div style="background-color:#0d1b2a;border:1px solid #1c2f45;border-radius:8px;
                    padding:2rem;text-align:center;">
            <p style="color:#7b8fa6;font-size:0.85rem;margin:0;">
                Tu portafolio está vacío. Ve a
                <strong style="color:#00b4d8">Zona de Inversión</strong> para comenzar.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# FRAGMENTO 2: Precio + calculadora (Zona de Inversión)
# ─────────────────────────────────────────────────────────

@st.fragment(run_every=60)
def precio_ticker_live(motor, simbolo: str, sesion, db, u_id: int) -> None:
    """
    Se refresca cada 60 s. Muestra precio actual, calculadora de operación
    y botones COMPRAR/VENDER para el ticker seleccionado.
    """
    precio_actual = motor.obtener_precio_actual(simbolo)

    # Guardar timestamp del precio para validación en calculos.py
    if precio_actual:
        st.session_state[f"_ts_precio_{simbolo}"] = time.time()
        st.session_state[f"_precio_{simbolo}"]    = precio_actual

    if precio_actual:
        # ── Calculadora ───────────────────────────────────
        st.markdown("""
        <p style="font-size:0.72rem;font-weight:600;letter-spacing:0.1em;
                  text-transform:uppercase;color:#7b8fa6;margin:1.2rem 0 0.6rem;">
        Calculadora de operación</p>
        """, unsafe_allow_html=True)

        c_val, c_cant, c_com, c_total = st.columns(4)
        with c_val:
            st.metric("Precio unitario", f"${precio_actual:,.2f}")
        with c_cant:
            cantidad = st.number_input(
                "Cantidad", min_value=1, step=1,
                label_visibility="visible",
                key=f"qty_{simbolo}",
            )

        monto_bruto = precio_actual * cantidad
        comision    = calcular_comision(monto_bruto)
        total_op    = monto_bruto + comision

        with c_com:
            st.metric("Comisión (0.5%)", f"${comision:,.2f}")
        with c_total:
            st.metric("Total estimado",  f"${total_op:,.2f}")

        # ── Botones ──────────────────────────────────────
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)
        col_compra, col_venta, _ = st.columns([1, 1, 2])

        with col_compra:
            st.markdown("""
            <style>
            div[data-testid="stButton"]:has(button:contains("COMPRAR")) button {
                background: linear-gradient(135deg,#0d2a26,#1a3a38)!important;
                border:1px solid #26a69a!important;color:#26a69a!important;
                font-weight:600!important;letter-spacing:0.05em!important;
            }
            div[data-testid="stButton"]:has(button:contains("COMPRAR")) button:hover {
                background:#26a69a!important;color:#060d1f!important;
            }
            </style>""", unsafe_allow_html=True)
            if st.button("▲ COMPRAR", width="stretch", key=f"btn_comprar_{simbolo}"):
                _ejecutar_compra(sesion, db, u_id, simbolo, cantidad, precio_actual)

        with col_venta:
            st.markdown("""
            <style>
            div[data-testid="stButton"]:has(button:contains("VENDER")) button {
                background: linear-gradient(135deg,#2a0d0d,#3a1a1a)!important;
                border:1px solid #ef5350!important;color:#ef5350!important;
                font-weight:600!important;letter-spacing:0.05em!important;
            }
            div[data-testid="stButton"]:has(button:contains("VENDER")) button:hover {
                background:#ef5350!important;color:#060d1f!important;
            }
            </style>""", unsafe_allow_html=True)
            if st.button("▼ VENDER", width="stretch", key=f"btn_vender_{simbolo}"):
                _ejecutar_venta(sesion, db, u_id, simbolo, cantidad, precio_actual)

        # ── Posición actual en este ticker ────────────────
        if simbolo in sesion.portafolio:
            pos       = sesion.portafolio[simbolo]
            valor_pos = pos["cantidad"] * precio_actual
            rend      = ((precio_actual - pos["precio_compra_promedio"])
                         / pos["precio_compra_promedio"]) * 100
            color_r   = "#26a69a" if rend >= 0 else "#ef5350"
            signo     = "▲" if rend >= 0 else "▼"

            st.markdown(f"""
            <div style="background-color:#0d1b2a;border:1px solid #1c2f45;
                        border-left:3px solid {color_r};border-radius:0 8px 8px 0;
                        padding:0.8rem 1.1rem;margin-top:1rem;
                        display:flex;gap:2rem;flex-wrap:wrap;">
                <div>
                    <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;
                              text-transform:uppercase;margin:0 0 0.15rem">Posición actual</p>
                    <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;
                              color:#e0e6f0;margin:0;font-weight:500">{pos['cantidad']} acciones</p>
                </div>
                <div>
                    <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;
                              text-transform:uppercase;margin:0 0 0.15rem">P. promedio compra</p>
                    <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;
                              color:#e0e6f0;margin:0;font-weight:500">${pos['precio_compra_promedio']:,.2f}</p>
                </div>
                <div>
                    <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;
                              text-transform:uppercase;margin:0 0 0.15rem">Valor actual</p>
                    <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;
                              color:#e0e6f0;margin:0;font-weight:500">${valor_pos:,.2f}</p>
                </div>
                <div>
                    <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.08em;
                              text-transform:uppercase;margin:0 0 0.15rem">Rendimiento</p>
                    <p style="font-family:'JetBrains Mono',monospace;font-size:0.95rem;
                              color:{color_r};margin:0;font-weight:600">{signo} {abs(rend):.2f}%</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Timestamp de última actualización
        st.caption(f"⟳ Precio actualizado: {time.strftime('%H:%M:%S')}  ·  próximo refresco en 60 s")

    else:
        st.markdown(f"""
        <div style="background-color:#1a0d0d;border:1px solid #3a1a1a;
                    border-radius:8px;padding:1rem 1.2rem;margin-top:0.5rem;">
            <p style="color:#ef5350;font-size:0.85rem;margin:0;">
                Ticker <strong>{simbolo}</strong> no encontrado.
                Verifica el símbolo e intenta de nuevo.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# FRAGMENTO 3: Saldo en sidebar
# ─────────────────────────────────────────────────────────

@st.fragment(run_every=60)
def precio_sidebar_live(sesion) -> None:
    """
    Se refresca cada 60 s. Muestra el saldo disponible actualizado en el sidebar.
    """
    saldo = sesion.saldo
    st.sidebar.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d2a26,#0d1b2a);
                border:1px solid #1c3a36;border-radius:8px;
                padding:1rem 1.1rem;margin-bottom:1.2rem;">
        <p style="font-size:0.65rem;color:#26a69a;letter-spacing:0.1em;
                  text-transform:uppercase;margin:0 0 0.2rem;">Saldo disponible</p>
        <p style="font-family:'JetBrains Mono',monospace;font-size:1.4rem;
                  font-weight:500;color:#e0e6f0;margin:0 0 0.15rem;">${saldo:,.2f}</p>
        <p style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
                  color:#3a4f63;margin:0;">⟳ {time.strftime('%H:%M:%S')}</p>
    </div>
    """, unsafe_allow_html=True)