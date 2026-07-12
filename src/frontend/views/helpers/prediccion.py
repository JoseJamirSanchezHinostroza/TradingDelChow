"""
frontend/views/helpers/prediccion.py - TradeaYa!
Pestaña de Predicción ML: busca cualquier ticker, entrena SVC en tiempo real
y muestra señal BUY/SELL con confianza, métricas del modelo y gráfico técnico.
Invocable con: from views.helpers.prediccion import mostrar_pantalla_prediccion
"""

import streamlit as st

from views.helpers.ml_grafico import _mostrar_grafico_ml

# Import diferido para no ralentizar el arranque de la app
# (ml_engine tarda ~0 s en importar; el cómputo ocurre solo al presionar Analizar)


# ─────────────────────────────────────────────────────────
# HELPERS DE UI
# ─────────────────────────────────────────────────────────

def _seccion_label(texto: str) -> None:
    """Etiqueta de sección en el estilo del dashboard."""
    st.markdown(f"""
    <p style="
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #7b8fa6;
        margin: 1rem 0 0.5rem;
    ">{texto}</p>
    """, unsafe_allow_html=True)


def _card_señal(señal: str, confianza: float, precio: float, fecha: str) -> None:
    """Card principal con la señal BUY/SELL y su confianza."""
    es_buy       = señal == "BUY"
    color        = "#26a69a" if es_buy else "#ef5350"
    bg           = "#0d2a26" if es_buy else "#2a0d0d"
    border       = "#1c3a36" if es_buy else "#3a1a1a"
    icono        = "▲" if es_buy else "▼"
    conf_pct     = f"{confianza * 100:.1f}%" if confianza is not None else "N/A"

    st.markdown(f"""
    <div style="
        background: {bg};
        border: 1px solid {border};
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1.2rem 1.5rem;
        display: flex;
        align-items: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    ">
        <div>
            <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.1em;
                      text-transform:uppercase;margin:0 0 0.2rem">Señal ML</p>
            <p style="font-family:'JetBrains Mono',monospace;font-size:2rem;
                      font-weight:700;color:{color};margin:0;line-height:1">
                {icono} {señal}
            </p>
        </div>
        <div>
            <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.1em;
                      text-transform:uppercase;margin:0 0 0.2rem">Confianza SVC</p>
            <p style="font-family:'JetBrains Mono',monospace;font-size:1.6rem;
                      font-weight:600;color:{color};margin:0">{conf_pct}</p>
        </div>
        <div>
            <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.1em;
                      text-transform:uppercase;margin:0 0 0.2rem">Último cierre</p>
            <p style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;
                      font-weight:500;color:#e0e6f0;margin:0">${precio:,.2f}</p>
        </div>
        <div>
            <p style="font-size:0.65rem;color:#3a4f63;letter-spacing:0.1em;
                      text-transform:uppercase;margin:0 0 0.2rem">Fecha referencia</p>
            <p style="font-family:'JetBrains Mono',monospace;font-size:0.9rem;
                      font-weight:400;color:#7b8fa6;margin:0">{fecha}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _card_metricas(metricas: dict, cv_f1: float, n_train: int, n_test: int,
                   fecha_corte: str, hiperparametros: dict) -> None:
    """Panel de métricas del modelo en 4 columnas."""
    acc  = metricas.get("accuracy",  0) or 0
    prec = metricas.get("precision", 0) or 0
    rec  = metricas.get("recall",    0) or 0
    f1   = metricas.get("f1",        0) or 0

    _seccion_label("Métricas del modelo SVC · Conjunto de prueba (20 %)")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Accuracy",  f"{acc  * 100:.1f}%")
    c2.metric("Precision", f"{prec * 100:.1f}%")
    c3.metric("Recall",    f"{rec  * 100:.1f}%")
    c4.metric("F1-Score",  f"{f1   * 100:.1f}%")

    # Detalle de configuración
    kernel = hiperparametros.get("svc__kernel", "—")
    C_val  = hiperparametros.get("svc__C",      "—")
    gamma  = hiperparametros.get("svc__gamma",  "—")
    cv_str = f"{cv_f1 * 100:.1f}%" if cv_f1 is not None else "N/A"

    st.markdown(f"""
    <div style="
        background-color: #0d1b2a;
        border: 1px solid #1c2f45;
        border-radius: 8px;
        padding: 0.8rem 1.2rem;
        margin-top: 0.6rem;
        display: flex;
        gap: 2rem;
        flex-wrap: wrap;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
    ">
        <div>
            <span style="color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase">
                Kernel</span>
            <span style="color:#00b4d8;margin-left:0.5rem;font-weight:500">{kernel}</span>
        </div>
        <div>
            <span style="color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase">
                C</span>
            <span style="color:#00b4d8;margin-left:0.5rem;font-weight:500">{C_val}</span>
        </div>
        <div>
            <span style="color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase">
                Gamma</span>
            <span style="color:#00b4d8;margin-left:0.5rem;font-weight:500">{gamma}</span>
        </div>
        <div>
            <span style="color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase">
                CV F1-macro</span>
            <span style="color:#00b4d8;margin-left:0.5rem;font-weight:500">{cv_str}</span>
        </div>
        <div>
            <span style="color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase">
                Train / Test</span>
            <span style="color:#7b8fa6;margin-left:0.5rem">{n_train} / {n_test} días</span>
        </div>
        <div>
            <span style="color:#3a4f63;letter-spacing:0.08em;text-transform:uppercase">
                Corte</span>
            <span style="color:#7b8fa6;margin-left:0.5rem">{fecha_corte}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _disclaimer() -> None:
    """Aviso legal en la parte inferior de la pestaña."""
    st.markdown("""
    <div style="
        margin-top: 1.5rem;
        padding: 0.7rem 1rem;
        background: rgba(0,180,216,0.04);
        border: 1px solid rgba(0,180,216,0.15);
        border-radius: 6px;
    ">
        <p style="
            font-size: 0.72rem;
            color: #3a4f63;
            letter-spacing: 0.04em;
            margin: 0;
        ">
            ⚠️ <strong style="color:#7b8fa6">DISCLAIMER:</strong>
            La señal BUY/SELL (COMPRA/VENTA) es generada por un Clasificador SVC entrenado con datos históricos
            de Yahoo Finance (2 años). El porcentaje de confianza refleja la probabilidad
            estimada del modelo, <em>no</em> una garantía de rentabilidad.
            TradeaYa! es un simulador educativo — así como ninguna operación representa una
            transacción real, ninguna predicción constituye asesoramiento financiero.
        </p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# FUNCIÓN PRINCIPAL (invocada desde dashboard.py)
# ─────────────────────────────────────────────────────────

def mostrar_pantalla_prediccion(lista_tickers: list) -> None:
    """
    Pestaña completa de Predicción ML.
    Recibe la lista de tickers ya cacheada del dashboard.
    """
    # ── Buscador ──────────────────────────────────────────────────────────────
    _seccion_label("Análisis predictivo de mercado")

    col_bus, col_man = st.columns([2, 1])
    with col_bus:
        opcion = st.selectbox(
            "Ticker ML",
            ["OTRO..."] + lista_tickers,
            label_visibility="collapsed",
            key="ml_selectbox",
        )
    with col_man:
        if opcion == "OTRO...":
            ticker_ml = st.text_input(
                "Ticker manual ML",
                placeholder="Ej: NVDA",
                label_visibility="collapsed",
                key="ml_ticker_manual",
            ).strip().upper()
        else:
            ticker_ml = opcion
            st.markdown(f"""
            <div style="
                background-color: #0d1b2a;
                border: 1px solid #1c2f45;
                border-radius: 6px;
                padding: 0.45rem 0.8rem;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.9rem;
                color: #00b4d8;
                font-weight: 500;
            ">{ticker_ml}</div>
            """, unsafe_allow_html=True)

    if not ticker_ml:
        st.markdown("""
        <div style="
            background-color: #0d1b2a;
            border: 1px solid #1c2f45;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
            margin-top: 1rem;
        ">
            <p style="color: #7b8fa6; font-size: 0.85rem; margin:0;">
                Ingresa un ticker para generar una predicción con Machine Learning.
            </p>
        </div>
        """, unsafe_allow_html=True)
        _disclaimer()
        return

    # ── Botón de análisis ─────────────────────────────────────────────────────
    st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)
    analizar = st.button(
        f"🤖 Analizar {ticker_ml} con SVC",
        type="primary",
        width="content",
        key="ml_btn_analizar",
    )

    # Mantener resultado en session_state para no re-entrenar en cada rerun
    cache_key = f"ml_resultado_{ticker_ml}"

    if analizar:
        st.session_state.pop(cache_key, None)   # forzar re-entrenamiento si se pulsa de nuevo

        with st.spinner(f"Descargando datos y entrenando SVC para {ticker_ml}… (puede tardar ~15–30 s)"):
            from logic.ml_engine import entrenar_y_predecir
            motor = st.session_state.motor   # TradeEngine — fuente única de datos
            resultado = entrenar_y_predecir(motor, ticker_ml)

        if resultado is None:
            st.error(
                f"No se pudo entrenar el modelo para **{ticker_ml}**. "
                "Verifica que el ticker sea válido y tenga al menos 80 sesiones de historia en yfinance."
            )
            return

        st.session_state[cache_key] = resultado

    # Mostrar resultado almacenado (evita re-entrenar en cada interacción de la UI)
    if cache_key not in st.session_state:
        _disclaimer()
        return

    res = st.session_state[cache_key]

    st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

    # ── Card de señal ─────────────────────────────────────────────────────────
    _card_señal(
        señal          = res["señal"],
        confianza      = res["confianza"],
        precio         = res["precio_vigente"],
        fecha          = res["fecha_vigente"],
    )

    # ── Gráfico técnico ───────────────────────────────────────────────────────
    _seccion_label("Gráfico técnico · Precio + SMA · RSI-14")
    _mostrar_grafico_ml(
        df_precio      = res["df_precio"],
        df_rsi         = res["df_rsi"],
        señal          = res["señal"],
        precio_vigente = res["precio_vigente"],
        ticker         = res["ticker"],
        ctx            = "pred",
    )

    # ── Métricas del modelo ───────────────────────────────────────────────────
    _card_metricas(
        metricas         = res["metricas"],
        cv_f1            = res["cv_f1_macro"],
        n_train          = res["n_train"],
        n_test           = res["n_test"],
        fecha_corte      = res["fecha_corte"],
        hiperparametros  = res["mejores_hiperparametros"],
    )

    _disclaimer()
