_TradeaYa! — Informe Final del Proyecto_ 

# **TradeaYa!** 

**Simulador de Trading Bursátil en Tiempo Real** 

_Informe Final del Proyecto_ 

Equipo: PeruDevs 

Integrantes: Abad Cuva David Eduardo (Backend) · Sánchez Hinostroza José Jamir (Frontend y Lógica) Julio 2026 

Página 1 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

## **1. Resumen Ejecutivo** 

TradeaYa! es una aplicación web desarrollada con Streamlit que simula un entorno real de trading bursátil sobre el mercado de valores de Estados Unidos. El sistema permite a los usuarios registrarse, autenticarse y operar (comprar y vender) acciones de empresas reales utilizando dinero ficticio, con datos de precios y de mercado obtenidos en tiempo real a través de la librería yfinance (Yahoo Finance). 

El objetivo del proyecto es ofrecer una experiencia formativa para futuros inversionistas: visualizar el comportamiento histórico de una acción mediante gráficos de velas japonesas, conocer su precio actual, y ejecutar órdenes de compra/venta que respetan reglas de negocio realistas (horario de mercado, comisiones, validación de saldo y de tenencias), todo ello sin exponer al usuario a riesgo financiero real. 

**Importante:** el proyecto NO utiliza la API de Alpaca. Aunque en una primera etapa de planificación se consideró su integración (y aún figura como dependencia en requirements.txt), la implementación final centraliza toda la obtención de precios, datos históricos y validación de tickers exclusivamente en Yahoo Finance a través de la librería yfinance, consumida desde la clase TradeEngine. 

## **2. Stack Tecnológico** 

El sistema está construido íntegramente en Python, con Streamlit como framework de interfaz web y una arquitectura organizada en tres capas: frontend, lógica de negocio (logic) y backend/datos. 

### **2.1 Lenguaje y framework principal** 

|**Componente**|**Tecnología**|**Función en elproyecto**|
|---|---|---|
|Lenguaje|Python 3.10+|Lenguaje único del proyecto, tanto para lógica como para<br>interfaz|
|Framework Web|Streamlit|Renderiza la interfaz, gestiona el estado de sesión y los<br>componentes interactivos|
|Datos de mercado|yfinance|Obtiene precios en tiempo real, históricos OHLCV y valida<br>tickers (Yahoo Finance)|
|Base de datos|SQLite / PostgreSQL|Persistencia local (SQLite) o en la nube vía Supabase<br>(PostgreSQL), detección automática|
|Gráficos|Plotly|Gráficos de velas japonesas interactivos para el historial de<br>precios|
|Manejo de datos|pandas|Manipulación de DataFrames para históricos, portafolio e<br>historial de transacciones|
|Zona horaria|pytz|Sincroniza el horario de mercado y los timestamps con<br>America/New_York|
|Variables de entorno|python-dotenv|Carga de configuración sensible(.env) para el backend|



### **2.2 Dependencias declaradas (requirements.txt)** 

El archivo de dependencias agrupa las librerías en tres bloques: conexión con el mercado, manejo de datos/reportes y utilidades generales. 

```
yfinance · pandas · openpyxl · pytz · python-dotenv · streamlit · websockets>=12.0 · watchdog ·
setuptools · wheel · numpy · plotly · psycopg2-binary
```

Página 2 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

### **2.3 Despliegue** 

La aplicación está preparada para funcionar tanto en entorno local como en Streamlit Community Cloud. La clase DatabaseManager detecta automáticamente el entorno de ejecución: si existe la variable de entorno DATABASE_URL, se conecta a una base de datos PostgreSQL (Supabase); en caso contrario, utiliza un archivo local SQLite (tradeaya.db). Esta doble configuración evita mantener dos versiones distintas del código para producción y desarrollo. 

## **3. Arquitectura del Sistema** 

El proyecto sigue una separación de responsabilidades en tres capas principales, ubicadas bajo el directorio src/, que favorece la mantenibilidad y permite testear la lógica de negocio de forma aislada de la interfaz. 

### **3.1 Estructura de carpetas** 

src/ 

├── frontend/ 



<!-- Start of picture text -->
│   ├── app.py                     # Punto de entrada, config de página y CSS global<br><!-- End of picture text -->

│   └── views/ │       ├── login.py                # Pantalla de login / registro │       ├── dashboard.py             # Pantalla principal (Portafolio + Zona de Inversión) │       └── helpers/ │           ├── sidebar.py           # Barra lateral: perfil, saldo, reloj de mercado │           ├── precio_live.py       # Fragmentos con auto-refresh (60 s) │           ├── grafico.py           # Gráfico de velas japonesas (Plotly) │           └── auxiliares.py        # Compra/venta, historial, lista de tickers ├── backend/ │   ├── trade_engine.py             # Puente con Yahoo Finance (precios, históricos) │   ├── database.py                 # Acceso a datos (SQLite/PostgreSQL) │   └── data_loader.py              # Exportación CSV/JSON (no integrado — ver abajo) └── logic/ ├── calculos.py                 # Reglas de negocio puras (comisiones, validaciones, horario) ├── portafolio.py               # Gestión en memoria del portafolio <mark>└── sesion.py                   # Clase SesionTrading: une calculos.py y portafolio.py</mark> 

### **3.2 Flujo general de la aplicación** 

El flujo de ejecución, desde que el usuario abre la aplicación hasta que realiza una operación, sigue estos pasos: 

- **1. Arranque:** app.py configura la página, inyecta el CSS del sistema de diseño global y crea (si no existen ya en session_state) las instancias únicas de DatabaseManager, SesionTrading, TradeEngine y DataLoader. 

- **2. Autenticación / persistencia de sesión:** si no hay un usuario activo, se intenta restaurar la sesión desde el parámetro uid en la URL (para sobrevivir a los reinicios de Streamlit Cloud); si no es posible, se muestra la pantalla de login. 

Página 3 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

- **3. Login o registro:** login.py valida credenciales contra la base de datos (verificar_login) o crea una cuenta nueva (registrar_usuario), con validación de formato de correo y longitud mínima de contraseña. 

- **4. Sincronización inicial:** al entrar al dashboard, se recupera desde la base de datos el saldo real del usuario y su portafolio persistido, y se cargan en el objeto SesionTrading de la sesión activa. 

- **5. Navegación por pestañas:** el dashboard se organiza en dos pestañas — “Portafolio” (resumen de posiciones e historial) y “Zona de Inversión” (búsqueda de tickers, gráfico y operativa de compra/venta). 

- **6. Actualización en vivo:** los precios, gráficos y métricas se refrescan automáticamente cada 60 segundos mediante fragmentos de Streamlit (st.fragment(run_every=60)), sin recargar toda la página; el reloj y estado del mercado en el sidebar se actualiza cada 1 segundo. 

- **7. Ejecución de una operación:** al comprar o vender, la UI delega la validación de reglas de negocio en SesionTrading (capa logic); si la operación es válida, se actualiza el estado en memoria y luego se persiste en la base de datos (DatabaseManager). 

- **8. Cierre de sesión:** el botón “Cerrar sesión” limpia el estado de sesión y los parámetros de la URL, devolviendo al usuario a la pantalla de login. 

### **3.3 Interacción entre capas** 

|**Capa**|**Responsabilidad**|**Depende de**|
|---|---|---|
|Frontend (views/)|Presentación, entrada de usuario, disparo de<br>acciones|logic, backend|
|Logic (logic/)|Reglas de negocio puras: validaciones, cálculos,<br>portafolio en memoria|Nada (independiente de<br>StreamlityDB)|
|Backend (backend/)|Acceso a datos externos: precios de mercado<br>(yfinance) y persistencia (DB)|Nada (independiente de la<br>UI)|



Esta separación permite que las reglas de negocio (por ejemplo, el cálculo de comisiones o la validación de una venta) puedan probarse y modificarse sin tocar la interfaz gráfica ni la base de datos, ya que logic/calculos.py y logic/portafolio.py no importan ni Streamlit ni DatabaseManager. 

## **4. Clases y Módulos Principales** 

### **4.1 SesionTrading (src/logic/sesion.py)** 

Es la clase central de la lógica de negocio. Se instancia una única vez por sesión de usuario activa y mantiene en memoria el estado de la operativa: saldo disponible, portafolio de acciones y el historial de operaciones realizadas durante la sesión. 

- **Atributos:** saldo (inicia en $10,000.00 según SALDO_INICIAL), portafolio (diccionario de posiciones) e historial (lista de operaciones). 

- **comprar():** recibe símbolo, cantidad, precio actual y timestamp del precio; delega la validación en calculos.validar_transaccion_compra y, si es exitosa, actualiza saldo y portafolio y registra la operación. 

- **vender():** análogo a comprar(), delega en calculos.validar_transaccion_venta, actualiza el saldo (suma el monto recibido) y reduce o elimina la posición correspondiente. 

- **get_resumen():** construye el diccionario que consume el dashboard: saldo disponible, valor del portafolio, patrimonio total, lista de posiciones con su rendimiento porcentual, y número total de operaciones. 

### **4.2 Módulo calculos.py (src/logic/calculos.py)** 

Contiene funciones puras (sin estado ni dependencias externas) que implementan las reglas de negocio del simulador: 

Página 4 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

- mercado_abierto(): determina si el mercado de EE. UU. está operativo (lunes a viernes, 9:30–16:00 hora de Nueva York). 

- calcular_comision(): aplica una comisión fija del 0.5% sobre el monto de cada operación. 

- es_precio_valido(): verifica que el precio utilizado no tenga una antigüedad mayor a 60 segundos (latencia máxima permitida). 

- calcular_monto_a_pagar() / calcular_monto_a_recibir(): calculan el monto neto de una compra o venta, incluyendo la comisión. 

- calcular_rendimiento(): calcula el rendimiento porcentual de una posición respecto a su precio de compra. 

- validar_transaccion_compra() / validar_transaccion_venta(): orquestan todas las validaciones anteriores y devuelven un resultado (éxito, mensaje, datos) que consume SesionTrading. 

### **4.3 Módulo portafolio.py (src/logic/portafolio.py)** 

Gestiona el portafolio del usuario como un diccionario en memoria, sin depender de la base de datos: 

- crear_portafolio(): inicializa un portafolio vacío al comenzar la sesión. 

- registrar_compra(): agrega una posición nueva o recalcula el precio de compra promedio ponderado si el símbolo ya existe. 

- registrar_venta(): reduce la cantidad de una posición o la elimina por completo si se vende la totalidad de las acciones. 

- obtener_posicion() / calcular_valor_portafolio(): funciones de consulta utilizadas para construir el resumen mostrado en el dashboard. 

### **4.4 TradeEngine (src/backend/trade_engine.py)** 

Es el único punto de contacto del sistema con datos de mercado externos. Encapsula todas las llamadas a la librería yfinance: 

- obtener_precio_actual(ticker): devuelve el último precio disponible de un símbolo, o None si ocurre un error. 

- obtener_datos_grafico(ticker, periodo): descarga el historial OHLCV (apertura, máximo, mínimo, cierre, volumen) para un periodo dado (1 día, 1 mes o 1 año), utilizado para construir el gráfico de velas. 

- validar_ticker(ticker): confirma si un símbolo bursátil existe y tiene información disponible en Yahoo Finance. 

### **4.5 DatabaseManager (src/backend/database.py)** 

Centraliza toda operación de persistencia del sistema, detectando automáticamente el motor de base de datos a utilizar (SQLite en local, PostgreSQL en la nube vía la variable de entorno DATABASE_URL) y adaptando los placeholders SQL (? para SQLite, %s para PostgreSQL) de forma transparente. 

- Gestión de usuarios: registrar_usuario() y verificar_login(). 

- Gestión de portafolio: obtener_portafolio(), guardar_compra() y guardar_venta(), que actualizan de forma atómica el saldo del usuario, el registro de la transacción y la posición en el portafolio. 

- Historial: obtener_historial(), que devuelve todas las transacciones del usuario ordenadas por fecha. 

- Creación de esquema: _crear_tablas() define las tablas usuarios, transacciones y portafolio, adaptando la sintaxis DDL según el motor detectado. 

### **4.6 DataLoader (src/backend/data_loader.py)** 

<mark>⚠</mark> _<mark>Módulo implementado a nivel de código, pero no integrado ni utilizado en la interfaz de usuario final. Se documenta su funcionalidad prevista, pero no se consideró su implementación completa para la entrega final del proyecto.</mark>_ 

Página 5 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

La clase DataLoader fue diseñada con el objetivo de permitir la exportación del historial de transacciones de un usuario a un archivo CSV o JSON, mediante el método exportar_historial_usuario(usuario_id, formato). Actualmente se instancia en app.py (st.session_state.loader) y queda disponible en el estado de la sesión, pero ningún componente del dashboard invoca sus métodos ni expone esta función al usuario final. 

Se considera una funcionalidad candidata para una futura actualización del sistema, en la que se agregaría a la interfaz un botón de “Exportar historial” dentro de la pestaña de Portafolio, permitiendo al usuario descargar su historial de operaciones en formato CSV o JSON directamente desde el dashboard. 

## **5. Modelo de Base de Datos** 

El esquema relacional está compuesto por tres tablas, creadas automáticamente al iniciar la aplicación si no existen (_crear_tablas), con sintaxis adaptada para SQLite o PostgreSQL según el entorno de ejecución. 

### **5.1 Tabla usuarios** 

|**Campo**|**Tipo**|**Descripción**|
|---|---|---|
|id|INTEGER / SERIAL (PK)|Identificador único autoincremental del usuario|
|nombre|TEXT|Nombre completo del usuario|
|email|TEXT (UNIQUE)|Correo electrónico, utilizado como credencial de<br>acceso|
|password|TEXT|Contraseña del usuario|
|saldo|REAL|Saldo disponible en dinero ficticio (por defecto<br>$10,000.00)|



### **5.2 Tabla transacciones** 

|**Campo**|**Tipo**|**Descripción**|
|---|---|---|
|id|INTEGER / SERIAL<br>(PK)|Identificador único de la transacción|
|usuario_id|INTEGER(FK)|Usuarioque realizó la operación|
|simbolo|TEXT|Ticker de la acción operada (ej. AAPL, TSLA)|
|cantidad|INTEGER|Cantidad de acciones compradas o vendidas|
|precio|REAL|Precio unitario al que se ejecutó la operación|
|tipo|TEXT|COMPRA o VENTA|
|fecha|TEXT|Fecha y hora de la operación (zona horaria de Nueva York)|



### **5.3 Tabla portafolio** 

|**Campo**|**Tipo**|**Descripción**|
|---|---|---|
|id|INTEGER / SERIAL<br>(PK)|Identificador único del registro|
|usuario_id|INTEGER(FK)|Usuariopropietario de laposición|



Página 6 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

|**Campo**|**Tipo**|**Descripción**|
|---|---|---|
|simbolo|TEXT|Ticker de la acción en cartera (único por usuario)|
|cantidad|INTEGER|Cantidad de accionesqueposee actualmente|
|precio_compra_promedio|REAL|Precio de compra promedio ponderado de la posición|



## **6. Reglas de Negocio Implementadas** 

Las siguientes reglas garantizan que la simulación se comporte de forma realista y consistente, y están implementadas de forma centralizada en el módulo logic/calculos.py: 

- **Validación de saldo:** una compra solo se ejecuta si el saldo disponible cubre el costo total de la operación (precio × cantidad) más la comisión correspondiente. 

- **Comisión de broker:** se aplica una comisión fija del 0.5% sobre el monto bruto de cada operación, tanto en compras como en ventas. 

- **Horario de mercado:** las operaciones de compra/venta solo se procesan si el mercado de EE. UU. está abierto (lunes a viernes, 9:30–16:00 hora de Nueva York); fuera de ese horario el sistema permite únicamente visualización. 

- **Propiedad de activos:** el usuario solo puede vender acciones que ya posee en su portafolio, y en cantidad igual o menor a la que tiene registrada. 

- **Frescura del precio:** toda operación exige que el precio utilizado tenga una antigüedad menor a 60 segundos, sincronizado con la frecuencia de actualización automática de la interfaz. 

## **7. Interfaz de Usuario** 

La interfaz fue construida sobre Streamlit, con un sistema de diseño global personalizado (definido mediante CSS inyectado en app.py) que reemplaza la apariencia por defecto de los componentes de Streamlit por una estética de terminal financiero oscuro. 

### **7.1 Sistema de diseño** 

|**Elemento**|**Valor**|**Uso**|
|---|---|---|
|Fondo principal|#060d1f|Color de fondo general de la aplicación|
|Superficie|#0d1b2a|Tarjetas, sidebar, métricas, inputs|
|Acento|#00b4d8|Elementos activos, enlaces, foco de inputs|
|Verde(compra /ganancia)|#26a69a|Botones de compra, rendimientospositivos|
|Rojo (venta / pérdida)|#ef5350|Botones de venta, rendimientos negativos|
|Tipografía|Inter / JetBrains Mono|Texto general (Inter) y datos numéricos (JetBrains<br>Mono)|



### **7.2 Pantalla de Login / Registro (login.py)** 

Presenta un encabezado con el logo y eslogan de la aplicación, y un panel central con dos pestañas: “Iniciar sesión” y “Crear cuenta”. El formulario de registro valida el formato del correo electrónico mediante expresión regular y exige una contraseña de al menos 6 caracteres antes de permitir el registro. 

Página 7 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

### **7.3 Dashboard principal (dashboard.py)** 

Una vez autenticado, el usuario accede a la pantalla principal, organizada en un sidebar persistente y dos pestañas de contenido: 

#### **Sidebar (helpers/sidebar.py)** 

- Tarjeta de cuenta activa: nombre del usuario e identificador de cuenta. 

- Saldo disponible, actualizado en vivo cada 60 segundos. 

- Reloj y estado del mercado (abierto/cerrado) en tiempo real, actualizado cada segundo, con zona horaria de Nueva York. 

- Indicación del horario de operación del mercado. 

- Botón de cierre de sesión. 

#### **Pestaña “Portafolio”** 

- Métricas: saldo disponible, valor del portafolio, patrimonio total y número de operaciones realizadas. 

- Tabla de posiciones abiertas, con precio de compra, precio actual y rendimiento porcentual (coloreado en verde/rojo). 

- Historial de operaciones desplegable, con todas las compras y ventas registradas. 

#### **Pestaña “Zona de Inversión”** 

- Buscador de tickers: selección desde la lista de símbolos del NASDAQ (con opción de ingreso manual). 

- Selector de periodo de análisis: 1 día (intradía), 1 mes o 1 año. 

- Gráfico de velas japonesas interactivo (Plotly), con métrica de variación de precio respecto al inicio del periodo. 

- Calculadora de compra/venta y botones de ejecución de la operación, con validación y mensajes de éxito/error mostrados como notificaciones (toast). 

### **7.4 Actualización en tiempo real** 

La interfaz utiliza fragmentos de Streamlit (st.fragment) para refrescar solo partes específicas de la pantalla sin recargar la aplicación completa: los precios, gráficos y métricas se actualizan cada 60 segundos, mientras que el reloj y estado del mercado en el sidebar se actualiza cada segundo. Esta estrategia mejora el rendimiento percibido y evita interrumpir al usuario mientras interactúa con otros elementos de la página. 

## **8. Distribución del Desarrollo por Integrante** 

|**Integrante**|**Rol**|**Responsabilidades**|
|---|---|---|
|Abad Cuva David<br>Eduardo|Backend|Servidor, gestión de datos, persistencia<br>(DatabaseManager) y conexión con la fuente de datos<br>de mercado (Yahoo Finance vía TradeEngine).|
|Sánchez Hinostroza José<br>Jamir|Frontend y Lógica|Lógica central de la aplicación, reglas de negocio<br>(logic/), interfaz gráfica, experiencia de usuario<br>(UX/UI) yvisualización de datos históricos.|



## **9. Alcance de la Entrega y Trabajo Futuro** 

### **9.1 Funcionalidades entregadas** 

Página 8 de 9 

_TradeaYa! — Informe Final del Proyecto_ 

- Registro y autenticación de usuarios, con persistencia de sesión ante recargas. 

- Visualización de precios en tiempo real y gráficos históricos (1 día, 1 mes, 1 año) de acciones reales del mercado estadounidense. 

- Simulación de compra y venta de acciones con dinero ficticio, aplicando comisión, validación de saldo, horario de mercado y frescura de precio. 

- Gestión de portafolio con cálculo de precio promedio ponderado y rendimiento por posición. 

- Persistencia de usuarios, portafolio e historial de transacciones, con soporte dual SQLite (local) / PostgreSQL (nube). 

- Interfaz gráfica personalizada con actualización automática en tiempo real. 

### **9.2 Funcionalidad no integrada en esta entrega** 

**Exportación de historial (DataLoader):** el módulo backend/data_loader.py ya contiene la lógica necesaria para exportar el historial de transacciones de un usuario a formato CSV o JSON. Sin embargo, esta funcionalidad no se conectó a la interfaz de usuario y no se consideró prioritaria para la entrega final del proyecto. Queda planteada como una mejora a implementar en una futura actualización, agregando un botón de descarga en la pestaña de Portafolio. 

Página 9 de 9 

