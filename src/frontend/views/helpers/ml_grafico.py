"""
frontend/views/helpers/ml_grafico.py - TradeaYa!
Gráfico Plotly para la pestaña de Predicción ML:
  - Panel superior : precio de cierre + SMA-20 + SMA-50 + línea de señal
  - Panel inferior : RSI-14 con bandas de sobrecompra/sobreventa
Recibe los DataFrames ya calculados por ml_engine.py.
"""

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def _mostrar_grafico_ml(
    df_precio: pd.DataFrame,
    df_rsi: pd.DataFrame,
    señal: str,
    precio_vigente: float,
    ticker: str,
    ctx: str = "ml",
) -> None:
    """
    Renderiza el gráfico técnico de la predicción ML.

    Parámetros:
        df_precio      : DataFrame con columnas close, sma_20, sma_50
        df_rsi         : DataFrame con columna rsi_14
        señal          : "BUY" o "SELL"
        precio_vigente : último precio de cierre
        ticker         : símbolo bursátil (para el key único)
        ctx            : prefijo de contexto para el key de Streamlit
    """
    color_señal = "#26a69a" if señal == "BUY" else "#ef5350"

    # ── Subplots: precio (70%) + RSI (30%) ────────────────────────────────────
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.70, 0.30],
        vertical_spacing=0.04,
    )

    # ── Panel superior: cierre + medias móviles ────────────────────────────────
    fig.add_trace(go.Scatter(
        x=df_precio.index,
        y=df_precio["close"],
        name="Cierre",
        line=dict(color="#e0e6f0", width=1.5),
        hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Cierre: $%{y:,.2f}<extra></extra>",
    ), row=1, col=1)

    if "sma_20" in df_precio.columns:
        fig.add_trace(go.Scatter(
            x=df_precio.index,
            y=df_precio["sma_20"],
            name="SMA-20",
            line=dict(color="#00b4d8", width=1, dash="dot"),
            hovertemplate="SMA-20: $%{y:,.2f}<extra></extra>",
        ), row=1, col=1)

    if "sma_50" in df_precio.columns:
        fig.add_trace(go.Scatter(
            x=df_precio.index,
            y=df_precio["sma_50"],
            name="SMA-50",
            line=dict(color="#f4a261", width=1, dash="dash"),
            hovertemplate="SMA-50: $%{y:,.2f}<extra></extra>",
        ), row=1, col=1)

    # Línea horizontal en el precio vigente (señal actual)
    fig.add_hline(
        y=precio_vigente,
        line_color=color_señal,
        line_width=1,
        line_dash="dot",
        row=1, col=1,
    )

    # Anotación de señal en el extremo derecho
    fig.add_annotation(
        x=df_precio.index[-1],
        y=precio_vigente,
        text=f" {señal}  ${precio_vigente:,.2f}",
        showarrow=False,
        xanchor="left",
        font=dict(color=color_señal, size=11, family="JetBrains Mono"),
        bgcolor="rgba(6,13,31,0.8)",
        bordercolor=color_señal,
        borderwidth=1,
        borderpad=4,
    )

    # ── Panel inferior: RSI-14 ─────────────────────────────────────────────────
    fig.add_trace(go.Scatter(
        x=df_rsi.index,
        y=df_rsi["rsi_14"],
        name="RSI-14",
        line=dict(color="#b39ddb", width=1.4),
        hovertemplate="RSI: %{y:.1f}<extra></extra>",
    ), row=2, col=1)

    # Banda sobrecompra (70) y sobreventa (30)
    for nivel, color, label in [(70, "#ef5350", "Sobrecompra"), (30, "#26a69a", "Sobreventa")]:
        fig.add_hline(
            y=nivel,
            line_color=color,
            line_width=0.8,
            line_dash="dash",
            row=2, col=1,
        )
        fig.add_annotation(
            x=df_rsi.index[0],
            y=nivel,
            text=f"{label} ({nivel})",
            showarrow=False,
            xanchor="left",
            yanchor="bottom",
            font=dict(color=color, size=9),
            row=2, col=1,
        )

    # Zona neutral RSI [30-70] sombreada
    fig.add_hrect(
        y0=30, y1=70,
        fillcolor="rgba(255,255,255,0.02)",
        line_width=0,
        row=2, col=1,
    )

    # ── Layout ─────────────────────────────────────────────────────────────────
    eje_x_comun = dict(
        showgrid=True,
        gridcolor="#1c2541",
        linecolor="#1c2541",
        tickformat="%b '%y",
        nticks=10,
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#0b132b",
        margin=dict(l=10, r=10, t=10, b=10),
        height=480,
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0, y=1.02,
            font=dict(size=10, color="#7b8fa6"),
            bgcolor="rgba(0,0,0,0)",
        ),
        xaxis=dict(**eje_x_comun, rangeslider=dict(visible=False)),
        xaxis2=dict(**eje_x_comun),
        yaxis=dict(
            showgrid=True,
            gridcolor="#1c2541",
            linecolor="#1c2541",
            side="right",
            autorange=True,
            fixedrange=True,
            tickprefix="$",
        ),
        yaxis2=dict(
            showgrid=True,
            gridcolor="#1c2541",
            linecolor="#1c2541",
            side="right",
            range=[0, 100],
            fixedrange=True,
            ticksuffix="",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False},
        key=f"{ctx}_{ticker}_ml_chart",
    )