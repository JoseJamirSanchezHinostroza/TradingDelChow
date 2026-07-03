"""
frontend/views/helpers/auxiliares.py - TradeaYa!
Funciones auxiliares para la construcción del Dashboard.
"""

import time
import pandas as pd
import streamlit as st


# ─────────────────────────────────────────────────────────
# TICKERS DISPONIBLES
# ─────────────────────────────────────────────────────────

@st.cache_data(ttl=86400)
def _obtener_todos_los_tickers() -> list:
    """Descarga los tickers del NASDAQ. Cachea por 24 h."""
    try:
        url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqtraded.txt"
        df  = pd.read_csv(url, sep="|")
        df  = df[df["Test Issue"] == "N"]
        tickers_crudos  = df["Symbol"].dropna().astype(str).tolist()
        tickers_limpios = [t for t in tickers_crudos if t.isalpha() and len(t) <= 5]
        return sorted(tickers_limpios)
    except Exception as e:
        st.error(f"Error al obtener tickers: {e}")
        return ["AAPL", "AMD", "AMZN", "MSFT", "NVDA", "TSLA"]


# ─────────────────────────────────────────────────────────
# EJECUCIÓN DE COMPRA
# ─────────────────────────────────────────────────────────

def _ejecutar_compra(sesion, db, u_id: int, simbolo: str, cantidad: int, precio_actual: float) -> None:
    """Valida y ejecuta una compra; la persiste en DB."""
    if precio_actual <= 0:
        st.error("Precio no disponible. Consulta el ticker antes de operar.")
        return

    costo_total = precio_actual * cantidad
    if sesion.saldo < costo_total:
        falta = costo_total - sesion.saldo
        st.error(f"Saldo insuficiente. Te faltan ${falta:,.2f}.")
        return

    nuevo_saldo = sesion.saldo - costo_total
    if db.guardar_compra(u_id, simbolo, cantidad, precio_actual, nuevo_saldo):
        sesion.comprar(simbolo, cantidad, precio_actual, time.time())
        st.toast(f"✅ {cantidad} × {simbolo} compradas a ${precio_actual:,.2f}", icon="🟩")
        time.sleep(1.2)
        st.rerun()
    else:
        st.error("Error al persistir la compra. Intenta de nuevo.")


# ─────────────────────────────────────────────────────────
# EJECUCIÓN DE VENTA
# ─────────────────────────────────────────────────────────

def _ejecutar_venta(sesion, db, u_id: int, simbolo: str, cantidad: int, precio_actual: float) -> None:
    """Valida y ejecuta una venta; la persiste en DB."""
    exito, msg = sesion.vender(simbolo, cantidad, precio_actual, time.time())

    if exito:
        if db.guardar_venta(u_id, simbolo, cantidad, precio_actual, sesion.saldo):
            st.toast(f"✅ {cantidad} × {simbolo} vendidas. {msg}", icon="🟥")
            time.sleep(1.2)
            st.rerun()
        else:
            st.error("Error al persistir la venta. Intenta de nuevo.")
    else:
        st.error(msg)


# ─────────────────────────────────────────────────────────
# PORTAFOLIO: MÉTRICAS + TABLA DE POSICIONES
# ─────────────────────────────────────────────────────────

def _mostrar_portafolio(sesion, motor) -> None:
    """Muestra las métricas de cuenta y la tabla de posiciones abiertas."""

    # Precios en vivo para todas las posiciones
    precios_vivos = {
        s: p
        for s in sesion.portafolio
        if (p := motor.obtener_precio_actual(s)) is not None
    }

    resumen    = sesion.get_resumen(precios_vivos)
    costo_inv  = sum(p["cantidad"] * p["precio_compra"] for p in resumen["posiciones"])
    ganancia   = resumen["valor_portafolio"] - costo_inv
    retorno_td = resumen["patrimonio_total"] - 10_000.00

    # ── Fila de métricas ──────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)

    k1.metric(
        label="Saldo disponible",
        value=f"${resumen['saldo_disponible']:,.2f}",
    )
    k2.metric(
        label="Valor del portafolio",
        value=f"${resumen['valor_portafolio']:,.2f}",
        delta=f"${ganancia:,.2f}" if costo_inv > 0 else None,
    )
    k3.metric(
        label="Patrimonio total",
        value=f"${resumen['patrimonio_total']:,.2f}",
        delta=f"${retorno_td:,.2f}",
    )
    k4.metric(
        label="Operaciones realizadas",
        value=resumen["total_operaciones"],
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # ── Tabla de posiciones ───────────────────────────────────────────────────
    if resumen["posiciones"]:
        st.markdown("""
        <p style="
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #7b8fa6;
            margin-bottom: 0.5rem;
        ">Posiciones abiertas</p>
        """, unsafe_allow_html=True)

        df = pd.DataFrame(resumen["posiciones"])
        df = df.rename(columns={
            "simbolo"       : "Símbolo",
            "cantidad"      : "Cant.",
            "precio_compra" : "P. Compra",
            "precio_actual" : "P. Actual",
            "rendimiento_%"  : "Rend. %",
        })
        df.index = range(1, len(df) + 1)

        # Formatters seguros: manejan None cuando el precio no está disponible
        fmt_precio = lambda v: f"${v:,.2f}" if v is not None else "N/A"
        fmt_rend   = lambda v: f"{v:+.2f}%" if v is not None else "N/A"

        st.dataframe(
            df.style.format({
                "P. Compra" : fmt_precio,
                "P. Actual" : fmt_precio,
                "Rend. %"   : fmt_rend,
            }).map(
                lambda v: "color: #26a69a" if isinstance(v, str) and v.startswith("+") else
                          ("color: #ef5350" if isinstance(v, str) and v.startswith("-") else ""),
                subset=["Rend. %"],
            ),
            width="stretch",
            height=min(80 + len(df) * 38, 400),
        )
    else:
        st.markdown("""
        <div style="
            background-color: #0d1b2a;
            border: 1px solid #1c2f45;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
        ">
            <p style="color: #7b8fa6; font-size: 0.85rem; margin:0;">
                Tu portafolio está vacío. Ve a <strong style="color:#00b4d8">Zona de Inversión</strong> para comenzar.
            </p>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# HISTORIAL DE OPERACIONES
# ─────────────────────────────────────────────────────────

def _mostrar_historial(db, u_id: int) -> None:
    """Muestra el historial completo de transacciones del usuario."""
    historial = db.obtener_historial(u_id)

    if historial:
        df = pd.DataFrame(historial, columns=["Acción", "Tipo", "Cant.", "Precio", "Fecha"])

        # Color por tipo de operación
        def _color_tipo(val):
            if val == "COMPRA":
                return "color: #26a69a; font-weight: 600"
            if val == "VENTA":
                return "color: #ef5350; font-weight: 600"
            return ""

        df.index = range(len(df), 0, -1)
        st.dataframe(
            df.style.format({"Precio": "${:.2f}"}).map(_color_tipo, subset=["Tipo"]),
            width="stretch",
            height=min(80 + len(df) * 38, 420),
        )
    else:
        st.markdown("""
        <div style="
            background-color: #0d1b2a;
            border: 1px solid #1c2f45;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
        ">
            <p style="color: #7b8fa6; font-size: 0.85rem; margin:0;">
                Aún no has realizado ninguna operación.
            </p>
        </div>
        """, unsafe_allow_html=True)
