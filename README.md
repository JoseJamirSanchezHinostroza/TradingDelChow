# 📈 TradeaYa!

Simulador de bolsa de valores con datos reales de mercado y dinero ficticio. Proyecto del curso **Algorítmica I** — Universidad Nacional Mayor de San Marcos.

> ⚠️ Exclusivamente para fines educativos. Mercado real, dinero ficticio. No se realizan transacciones reales.

---

## ✨ Funcionalidades

- **Autenticación**: registro e inicio de sesión con persistencia entre recargas (Streamlit Community Cloud incluido).
- **Terminal de inversión**: búsqueda de tickers (NASDAQ), gráfico de velas japonesas (1 día / 1 mes / 1 año), calculadora de operación y botones de compra/venta.
- **Portafolio**: saldo disponible, valor de posiciones, patrimonio total, rendimiento por acción e historial completo de operaciones.
- **Datos en vivo**: precios, métricas y reloj de mercado (hora de Nueva York) se auto-refrescan cada 60 segundos mediante `st.fragment`, sin recargar la página completa.
- **Persistencia híbrida**: SQLite en local, PostgreSQL (Supabase) en producción — detección automática de entorno.

## 🧱 Stack

| Capa | Tecnología |
|---|---|
| Interfaz | [Streamlit](https://streamlit.io) |
| Datos de mercado | [yfinance](https://pypi.org/project/yfinance/) (Yahoo Finance) |
| Gráficos | [Plotly](https://plotly.com/python/) |
| Datos | Pandas / NumPy |
| Base de datos | SQLite (local) · PostgreSQL vía Supabase (Cloud) |
| Zona horaria | pytz (America/New_York) |

## 🗂️ Estructura del proyecto

```
src/
├── frontend/
│   ├── app.py                     # Punto de entrada, config de página y CSS global
│   └── views/
│       ├── login.py                # Pantalla de login / registro
│       ├── dashboard.py             # Pantalla principal (Portafolio + Zona de Inversión)
│       └── helpers/
│           ├── sidebar.py           # Barra lateral: perfil, saldo, reloj de mercado
│           ├── precio_live.py       # Fragmentos con auto-refresh (60 s)
│           ├── grafico.py           # Gráfico de velas japonesas (Plotly)
│           └── auxiliares.py        # Compra/venta, historial, lista de tickers
├── backend/
│   ├── trade_engine.py             # Puente con Yahoo Finance (precios, históricos)
│   ├── database.py                 # Acceso a datos (SQLite/PostgreSQL)
│   └── data_loader.py              # Exportación CSV/JSON (no integrado — ver abajo)
└── logic/
    ├── calculos.py                 # Reglas de negocio puras (comisiones, validaciones, horario)
    ├── portafolio.py               # Gestión en memoria del portafolio
    └── sesion.py                   # Clase SesionTrading: une calculos.py y portafolio.py
```

La arquitectura se divide en tres capas independientes:

- **`logic/`** — funciones puras de Python, sin Streamlit ni base de datos. Reglas de negocio testeables de forma aislada.
- **`backend/`** — comunicación con el exterior: API de precios y base de datos.
- **`frontend/`** — interfaz gráfica, orquesta llamadas a `logic/` y `backend/`.

## 📐 Reglas de negocio

| Regla | Descripción |
|---|---|
| Horario de mercado | Lunes a viernes, 9:30–16:00 hora de Nueva York |
| Comisión | 0.5 % por operación |
| Frescura del precio | Máximo 60 s de antigüedad para operar |
| Saldo | No se permite comprar por encima del saldo disponible |
| Propiedad de activos | Solo se vende lo que existe en el portafolio |
| Precio promedio | Se recalcula ponderado en cada nueva compra del mismo ticker |

## 🚀 Cómo ejecutar en local

```bash
# 1. Clonar el repositorio
git clone <url-del-repo>
cd tradingdelchow

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar
streamlit run src/frontend/app.py
```

La app crea automáticamente un archivo `tradeaya.db` (SQLite) en la raíz del proyecto la primera vez que se ejecuta.

## ☁️ Despliegue en Streamlit Community Cloud

1. Configurar en **App Settings → Secrets** la variable `DATABASE_URL` apuntando a la instancia de PostgreSQL (Supabase). Su presencia activa automáticamente el modo Cloud en `DatabaseManager`.
2. Tras cualquier cambio estructural en los paquetes (`__init__.py`), usar **Reboot app** en vez de un simple redeploy, ya que Streamlit Cloud puede cachear el estado de namespace packages.

## 🔌 Funcionalidad disponible pero no integrada

`DataLoader` (`src/backend/data_loader.py`) exporta el historial de transacciones a CSV/JSON y está completamente operativo, pero no se conectó a la interfaz en esta entrega por no ser parte del alcance mínimo. Queda como mejora **Plus** para una futura actualización (por ejemplo, un botón de descarga en el historial de operaciones).

## 👥 Equipo — PeruDevs

- **Sánchez Hinostroza, José Jamir** — Lógica y Frontend
- **Abad Cuva, David Eduardo** — Backend

## 📄 Documentación adicional

- `pautas/Directivas del Proyecto Grupal.md`
- `pautas/Rubricas del proyecto final.md`
- `Entregables/` — entregables previos del curso
