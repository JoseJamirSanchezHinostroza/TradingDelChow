"""
logic/ml_engine.py - TradeaYa!
Motor de Machine Learning: obtiene datos OHLCV desde el backend (TradeEngine),
calcula indicadores técnicos (SMA, EMA, RSI), entrena un clasificador SVC
con GridSearchCV + TimeSeriesSplit y devuelve señal BUY/SELL con confianza.

Basado en la investigación InvestAI (Notebook2_SVC_MongoDB.ipynb).
Fuente de datos: backend/trade_engine.py → yfinance (centralizado).
"""

import math
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
)

# ─────────────────────────────────────────────────────────
# CONFIGURACIÓN DEL MODELO
# ─────────────────────────────────────────────────────────

RATIO_TRAIN   = 0.80      # 80 % entrenamiento / 20 % prueba (partición temporal)
CV_FOLDS      = 5         # Folds para TimeSeriesSplit
MIN_REGISTROS = 80        # Mínimo de registros válidos para entrenar

PARAM_GRID = {
    "svc__kernel": ["linear", "rbf"],
    "svc__C":      [0.1, 1, 10, 100],
    "svc__gamma":  ["scale", "auto"],
}

COLUMNAS_INDICADORES = ["sma_20", "sma_50", "ema_12", "ema_26", "rsi_14"]

COLUMNAS_FEATURES = COLUMNAS_INDICADORES + [
    "retorno_1d", "rango_intradia",
    "precio_sobre_sma20", "precio_sobre_sma50", "cruce_ema",
]


# ─────────────────────────────────────────────────────────
# SECCIÓN 1: Descarga y preparación OHLCV
# ─────────────────────────────────────────────────────────

def _obtener_ohlcv_del_backend(motor, ticker: str, periodo: str = "2y") -> pd.DataFrame | None:
    """
    Obtiene datos OHLCV del ticker a través del backend centralizado (TradeEngine).
    Usa 2 años para garantizar suficientes registros tras el calentamiento de SMA-50.
    Devuelve DataFrame con columnas minúsculas: open, high, low, close, volume.
    motor: instancia de TradeEngine (st.session_state.motor)
    """
    try:
        hist = motor.obtener_datos_grafico(ticker, periodo=periodo)
        if hist is None or (hasattr(hist, "empty") and hist.empty):
            return None
        hist = hist.copy()
        hist.columns = [c.lower() for c in hist.columns]
        hist.index   = pd.to_datetime(hist.index)
        if hist.index.tz is not None:
            hist.index = hist.index.tz_localize(None)
        cols_requeridas = {"open", "high", "low", "close", "volume"}
        if not cols_requeridas.issubset(set(hist.columns)):
            return None
        if len(hist) < MIN_REGISTROS:
            return None
        return hist[["open", "high", "low", "close", "volume"]].copy()
    except Exception:
        return None


# ─────────────────────────────────────────────────────────
# SECCIÓN 2: Indicadores técnicos
# ─────────────────────────────────────────────────────────

def _calcular_rsi(serie: pd.Series, periodo: int = 14) -> pd.Series:
    """RSI con EWM (mismo comportamiento que ta-lib)."""
    delta = serie.diff()
    ganancia = delta.clip(lower=0)
    perdida  = (-delta).clip(lower=0)
    rs = (
        ganancia.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
        / perdida.ewm(alpha=1 / periodo, min_periods=periodo, adjust=False).mean()
    )
    return 100 - (100 / (1 + rs))


def _calcular_indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade SMA-20, SMA-50, EMA-12, EMA-26, RSI-14 al DataFrame OHLCV.
    Todos calculados solo con datos pasados (sin data leakage).
    """
    d = df.copy()
    d["sma_20"] = d["close"].rolling(20).mean()
    d["sma_50"] = d["close"].rolling(50).mean()
    d["ema_12"] = d["close"].ewm(span=12, adjust=False).mean()
    d["ema_26"] = d["close"].ewm(span=26, adjust=False).mean()
    d["rsi_14"] = _calcular_rsi(d["close"], 14)
    return d


# ─────────────────────────────────────────────────────────
# SECCIÓN 3: Features y target
# ─────────────────────────────────────────────────────────

def _construir_features_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye el conjunto de features + target binario.

    target = 1 (BUY)  si el cierre de MAÑANA > cierre de HOY
    target = 0 (SELL) en caso contrario

    La última fila (sin target conocido) se conserva aparte
    para generar la señal vigente. Sin data leakage.
    """
    d = df.copy()
    d["cierre_manana"]       = d["close"].shift(-1)
    d["target"]              = (d["cierre_manana"] > d["close"]).astype(int)
    d["retorno_1d"]          = d["close"].pct_change(1)
    d["rango_intradia"]      = (d["high"] - d["low"]) / d["close"]
    d["precio_sobre_sma20"]  = d["close"] / d["sma_20"] - 1
    d["precio_sobre_sma50"]  = d["close"] / d["sma_50"] - 1
    d["cruce_ema"]           = d["ema_12"] / d["ema_26"] - 1
    return d


# ─────────────────────────────────────────────────────────
# SECCIÓN 4: Utilidad numérica
# ─────────────────────────────────────────────────────────

def _nan_a_none(valor) -> float | None:
    """Convierte NaN/Inf a None; redondea floats a 6 decimales."""
    if valor is None:
        return None
    try:
        if math.isnan(valor) or math.isinf(valor):
            return None
        return round(float(valor), 6)
    except (TypeError, ValueError):
        return None


# ─────────────────────────────────────────────────────────
# SECCIÓN 5: Pipeline completo SVC
# ─────────────────────────────────────────────────────────

def entrenar_y_predecir(motor, ticker: str) -> dict | None:
    """
    Pipeline completo para cualquier ticker:
      1. Obtiene OHLCV (2 años) desde el backend (TradeEngine → yfinance)
      2. Calcula SMA-20, SMA-50, EMA-12, EMA-26, RSI-14
      3. Construye features y target binario (sin data leakage)
      4. Partición temporal 80/20
      5. StandardScaler + SVC optimizado con GridSearchCV (TimeSeriesSplit)
      6. Evaluación en test (accuracy, precision, recall, f1)
      7. Predicción de la señal vigente (BUY/SELL) con confianza

    motor  : instancia de TradeEngine (st.session_state.motor)
    ticker : símbolo bursátil
    Devuelve dict con señal, confianza, métricas y datos para gráfico,
    o None si no hay datos suficientes.
    """
    # ── Paso 1-2: Datos del backend + indicadores ─────────────────────────────
    df_raw = _obtener_ohlcv_del_backend(motor, ticker)
    if df_raw is None:
        return None

    df_ind = _calcular_indicadores(df_raw)

    # ── Paso 3: Features + target ─────────────────────────────────────────────
    df_feat = _construir_features_target(df_ind)

    # Fila más reciente: features OK pero target desconocido (es "mañana")
    fila_vigente = df_feat.iloc[[-1]].copy()

    # Conjunto de modelo: descarta NaN en features Y en target
    df_modelo = df_feat.dropna(subset=COLUMNAS_FEATURES + ["target"]).copy()

    if len(df_modelo) < MIN_REGISTROS:
        return None

    # ── Paso 4: Partición temporal (sin shuffle) ──────────────────────────────
    n      = len(df_modelo)
    corte  = int(n * RATIO_TRAIN)
    df_tr  = df_modelo.iloc[:corte]
    df_te  = df_modelo.iloc[corte:]

    if len(df_te) < 5:
        return None

    X_train = df_tr[COLUMNAS_FEATURES].values
    y_train = df_tr["target"].values
    X_test  = df_te[COLUMNAS_FEATURES].values
    y_test  = df_te["target"].values

    # Fila vigente: puede tener NaN en precio_sobre_sma50 si hay pocos datos
    X_vigente = fila_vigente[COLUMNAS_FEATURES].values
    if np.isnan(X_vigente).any():
        return None

    # ── Paso 5: Pipeline StandardScaler + SVC con GridSearchCV ───────────────
    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("svc",    SVC(probability=True, random_state=42, cache_size=500)),
    ])

    n_splits = min(CV_FOLDS, max(2, len(X_train) // 20))
    tscv     = TimeSeriesSplit(n_splits=n_splits)

    grid = GridSearchCV(
        estimator  = pipeline,
        param_grid = PARAM_GRID,
        cv         = tscv,
        scoring    = "f1_macro",
        n_jobs     = -1,
        refit      = True,
    )
    grid.fit(X_train, y_train)
    modelo     = grid.best_estimator_
    mejores_p  = grid.best_params_
    cv_f1      = grid.best_score_

    # ── Paso 6: Evaluación en test ────────────────────────────────────────────
    y_pred = modelo.predict(X_test)
    acc    = accuracy_score(y_test, y_pred)
    prec   = precision_score(y_test, y_pred, zero_division=0)
    rec    = recall_score(y_test, y_pred, zero_division=0)
    f1     = f1_score(y_test, y_pred, zero_division=0)

    # ── Paso 7: Señal vigente ─────────────────────────────────────────────────
    prob_vigente  = modelo.predict_proba(X_vigente)[0]
    pred_vigente  = modelo.predict(X_vigente)[0]
    señal         = "BUY" if pred_vigente == 1 else "SELL"
    confianza     = float(prob_vigente[1]) if pred_vigente == 1 else float(prob_vigente[0])

    return {
        # Señal principal
        "ticker"          : ticker,
        "señal"           : señal,
        "confianza"       : _nan_a_none(confianza),
        "precio_vigente"  : _nan_a_none(fila_vigente["close"].iloc[0]),
        "fecha_vigente"   : fila_vigente.index[0].strftime("%Y-%m-%d"),

        # Métricas del modelo
        "metricas": {
            "accuracy"  : _nan_a_none(acc),
            "precision" : _nan_a_none(prec),
            "recall"    : _nan_a_none(rec),
            "f1"        : _nan_a_none(f1),
        },
        "cv_f1_macro"          : _nan_a_none(cv_f1),
        "mejores_hiperparametros": mejores_p,
        "n_train"              : int(len(df_tr)),
        "n_test"               : int(len(df_te)),
        "fecha_corte"          : df_tr.index[-1].strftime("%Y-%m-%d"),

        # Datos para el gráfico
        "df_precio"   : df_ind[["close", "sma_20", "sma_50", "ema_12", "ema_26"]].dropna(subset=["close"]),
        "df_rsi"      : df_ind[["rsi_14"]].dropna(),
        "df_volumen"  : df_ind[["volume"]].dropna(),
    }