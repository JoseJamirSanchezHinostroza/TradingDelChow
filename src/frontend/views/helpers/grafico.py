"""
frontend/views/helpers/grafico.py - TradeaYa!
Función que grafica el historial de precios de un activo financiero durante un periodo seleccionado utilizando Plotly y Streamlit.
Recibe el motor de la API, el Ticker y el Periodo.
"""

import time # Librería de tiempo
import pandas as pd # Pandas para tablas de datos
import streamlit as st # Streamlit como motor gráfico de la página web
import plotly.graph_objects as go # Plotly para gráficos avanzados de velas japonesas

def _mostrar_grafico(motor, simbolo: str, periodo: str) -> None:
    
    nombres_periodo = {"1d": "Hoy (Intradía)", "1mo": "Último Mes", "1y": "Último Año"}
    
    try:
        datos_hist = motor.obtener_datos_grafico(simbolo, periodo=periodo) # Petición al motor de precios el historial del último mes
        
        if datos_hist is not None and (not datos_hist.empty if hasattr(datos_hist, 'empty') else datos_hist): # Si existen los datos
            
            if isinstance(datos_hist, dict): # Si el motor devuelve un diccionario o serie se convierte a DataFrame
                df = pd.DataFrame(list(datos_hist.items()), columns=["Fecha", "Close"]).set_index("Fecha")
            elif isinstance(datos_hist, pd.Series):
                df = datos_hist.to_frame(name="Close")
            else:
                df = datos_hist.copy()

            df.columns = [str(c).lower() for c in df.columns] # Forzar columnas a minúsculas para evitar fallos de coincidencia
            df.index = pd.to_datetime(df.index)
            col_cierre = "close" if "close" in df.columns else df.columns[0] # Asegurar que 'close' exista
            variacion = ((df[col_cierre].iloc[-1] - df[col_cierre].iloc[0]) / df[col_cierre].iloc[0]) * 100 # Cálculo de la variacion de precios entre hoy[-1] y hace 1 mes[0]
            
            st.metric( # Métrica dinámica sobre el gráfico que muestra el precio actual y la variación respecto al inicio del periodo
                label=f"Precio Actual {nombres_periodo[periodo]}", 
                value=f"${df[col_cierre].iloc[-1]:,.2f}", # Precio final del periodo
                delta=f"${df[col_cierre].iloc[-1]-df[col_cierre].iloc[0]:,.2f} ({variacion:+.2f}%)" # Variación en absoluto y porcentaje
            )

            fig = go.Figure() # Gráfico de velas japonesas con Plotly

            if 'volume' in df.columns and df['volume'].max() > 0:
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['volume'],
                    name='Volume',
                    marker_color='rgba(0, 180, 216, 0.18)', # Barras de volumen en gris claro
                    yaxis='y2', # Segundo eje Y para el volumen
                    hoverinfo='skip'
                ))

            if all(col in df.columns for col in ["open", "high", "low", "close"]): # Si YFinance brinda el DF completo OHLC dibuja las velas
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    increasing_line_color='#26a69a', # Verde TradingView
                    decreasing_line_color='#ef5350', # Rojo TradingView
                    name="Precio"
                ))

            fig.update_layout( # Estilo profesional
                template='plotly_dark',
                paper_bgcolor='rgba(0,0,0,0)', # Fondo transparente para integración con Streamlit
                plot_bgcolor='#0b132b', # Azul oscuro profundo para el background del gráfico
                margin=dict(l=10, r=10, t=10, b=10),
                height=420,
                xaxis=dict(
                    showgrid=True, 
                    gridcolor='#1c2541',       # Rejilla sutil azulada/neon
                    linecolor='#1c2541',
                    rangeslider=dict(visible=False), # Oculta la barra de abajo que quita espacio
                    type='category', 
                    tickvals=df.index, 
                    ticktext=[d.strftime('%b %d') for d in df.index],
                    tickformat='%b %d' if periodo == "1mo" else ('%H:%M' if periodo == "1d" else None),
                    nticks=8,
                    tickangle=0
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#1c2541', 
                    linecolor='#1c2541',
                    side='right',               # Precios a la derecha (Estándar de Pro-Trading)
                    autorange=True, # Autoescalado para ajustar al rango de precios
                    fixedrange=True
                ),
                yaxis2=dict(
                    overlaying='y', # Superpuesto en el gráfico
                    side='left', # Volumen a la izquierda para diferenciar de los precios
                    showgrid=False,
                    showticklabels=False,
                    range=[0, float(df['volume'].max()*4)] if ('volume' in df.columns and df['volume'].max() > 0) else [0, 1]
                ),
                hovermode='x unified',
                showlegend=False
            )

            # Renderización en Streamlit
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.caption(f"Variación del periodo: **{variacion:+.2f}%**")

        else:
            st.warning(f"Sin historial disponible para {simbolo} en el periodo '{periodo}'.") # No hay datos
    except Exception as e:
        st.error(f"Error procesando gráfico profesional: {e}") # Fallo de la API/Internet