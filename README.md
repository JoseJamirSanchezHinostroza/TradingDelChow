# TradeaYa! - PeruDevs
## 1. Descripción de las funcionalidades del proyecto:
### TradeaYa! es una aplicación que permite al usuario interactuar con el mercado de acciones de E.E.U.U. a través de un simulador de bolsa de valores en tiempo real.
### En esta app, es posible visualizar los precios de las acciones más relevantes del mercado (Apple, Tesla, etc.) en tiempo real y operar sobre ellas con dinero ficticio gracias a *Alpaca API*.
### Además, implementamos *Yahoo Finance API*, cuya función es proporcionar los datos históricos de dichas acciones. Así, el usuario obtiene la experiencia completa: analiza el comportamiento histórico de las acciones, revisa el precio actual de la acción de su interés y compra/vende utilizando dinero ficticio.
### TradeaYa! es el simulador definitivo para futuros *traders*: permite desarrollar estrategias de inversión sin riesgo financiero real.
## 2. Reglas del Negocio:
### Se implementarán las siguientes reglas en el proyecto, de manera que puedan asegurar el correcto funcionamiento del mismo.
### Validación de Saldo: El sistema no permitirá compras si el costo total de la transacción (precio de acción x cantidad) más la comisión excede el saldo disponible en la cuenta ficticia.
### Gestión de Comisiones: Se aplicará una comisión fija o porcentual por cada operación realizada (ej. 0.5% por transacción) para simular los costos operativos de un broker real.
### Horario de Mercado: Las operaciones de compra/venta solo se procesarán si el mercado de EE. UU. está abierto (Lunes a Viernes, 9:30 AM - 4:00 PM EST). Fuera de este horario, el sistema solo permitirá visualización.
### Propiedad de Activos: El usuario solo podrá vender acciones que existan previamente en su portafolio y en cantidades iguales o menores a las que posee.
### Actualización de Precios: Los precios de mercado deben refrescarse con una latencia máxima definida (ej. cada 15-60 segundos) para asegurar que la toma de decisiones se base en datos recientes.
## 3. Distribución del desarrollo por integrante:
### Abad David(BackEnd): Se encargará del servidor y la gestión de datos necesarios para operar, además de establecer y mantener la conexión con las API's de Alpaca y Yahoo Finance.
### Ramirez Jeremi(FrontEnd): Se encargará de la parte gráfica y la experiencia de usuario (UX/UI). Su objetivo es presentar una interfaz gráfica intuitiva, moderna y atractiva para el consumidor, graficando datos historícos de manera clara.
### Sánchez José(Algoritmos): Se encargará de la lógica central de la aplicación. Traducirá las reglas del negocio en código y creará algoritmos matemáticos que calculen comisiones, validen saldos y gestionen el portafolio ficticio del usuario de forma precisa.
