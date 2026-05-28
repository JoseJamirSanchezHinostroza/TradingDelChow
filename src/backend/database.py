"""
backend/database.py - TradeaYa!
Capa de acceso a datos: usuarios, portafolio y transacciones.
Toda operación con SQLite pasa por aquí.
"""

import sqlite3                  # Módulo estándar de Python para trabajar con bases de datos SQLite sin servidor externo
from datetime import datetime   # Clase para obtener y manipular fechas y horas actuales
import pytz                     # Librería para manejo de zonas horarias (no incluida en Python estándar; permite conversiones precisas)


class DatabaseManager:
    """Gestiona la conexión y operaciones sobre la base de datos SQLite."""

    def __init__(self, db_name: str = "tradeaya.db") -> None:   # Constructor: acepta el nombre del archivo DB; si no se pasa ninguno, usa "tradeaya.db" por defecto
        self.db_name = db_name                                   # Guarda el nombre del archivo como atributo de instancia para usarlo en cada conexión
        self._crear_tablas()                                     # Llama al método privado que crea las tablas al iniciar (si aún no existen)

    # ─────────────────────────────────────────────────────────
    # CONEXIÓN
    # ─────────────────────────────────────────────────────────

    def conectar(self) -> sqlite3.Connection:                    # Método que devuelve un objeto Connection listo para ejecutar consultas SQL
        """Devuelve una conexión con timeout para evitar 'database is locked'."""
        return sqlite3.connect(self.db_name, timeout=10)         # Abre (o crea) el archivo .db; timeout=10 espera hasta 10 segundos si la DB está bloqueada por otro proceso

    # ─────────────────────────────────────────────────────────
    # INICIALIZACIÓN DE TABLAS
    # ─────────────────────────────────────────────────────────

    def _crear_tablas(self) -> None:                             # Método privado (convención: guión bajo al inicio); solo se llama desde __init__
        """Crea las tablas si no existen. Se llama una sola vez al iniciar."""
        with self.conectar() as conn:                            # Abre la conexión usando context manager: hace commit automático al salir o rollback si hay error
            conn.executescript("""                               
                CREATE TABLE IF NOT EXISTS usuarios (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,  -- Identificador único que se incrementa automáticamente con cada nuevo registro
                    nombre   TEXT    NOT NULL,                   -- Nombre del usuario; NOT NULL obliga a que siempre tenga valor
                    email    TEXT    UNIQUE NOT NULL,            -- Email del usuario; UNIQUE impide correos duplicados en la tabla
                    password TEXT    NOT NULL,                   -- Contraseña del usuario almacenada en texto plano
                    saldo    REAL    DEFAULT 100000.0            -- Saldo inicial en dólares; si no se especifica al crear el usuario, se asigna $100,000
                );

                CREATE TABLE IF NOT EXISTS transacciones (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,  -- Identificador único de cada transacción
                    usuario_id INTEGER NOT NULL,                    -- ID del usuario que realizó la operación (referencia lógica a usuarios.id)
                    simbolo    TEXT    NOT NULL,                    -- Ticker bursátil de la acción operada (ej: "AAPL", "MSFT")
                    cantidad   INTEGER NOT NULL,                    -- Número de acciones compradas o vendidas
                    precio     REAL    NOT NULL,                    -- Precio unitario de la acción al momento de la operación
                    tipo       TEXT    NOT NULL,                    -- Indica si fue "COMPRA" o "VENTA"
                    fecha      TEXT    NOT NULL                     -- Fecha y hora de la operación en formato texto "YYYY-MM-DD HH:MM:SS"
                );

                CREATE TABLE IF NOT EXISTS portafolio (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,   -- Identificador único de cada fila del portafolio
                    usuario_id             INTEGER,                  -- ID del usuario dueño de esta posición
                    simbolo                TEXT    NOT NULL,         -- Ticker de la acción que el usuario posee actualmente
                    cantidad               INTEGER NOT NULL,         -- Cantidad de acciones que el usuario tiene en cartera
                    precio_compra_promedio REAL    NOT NULL,         -- Precio promedio ponderado de todas las compras realizadas de ese ticker
                    FOREIGN KEY(usuario_id) REFERENCES usuarios(id), -- Restricción de integridad: usuario_id debe existir en la tabla usuarios
                    UNIQUE(usuario_id, simbolo)                      -- Impide duplicados: cada usuario solo puede tener una fila por ticker
                );
            """)

    # ─────────────────────────────────────────────────────────
    # USUARIOS
    # ─────────────────────────────────────────────────────────

    def registrar_usuario(self, nombre: str, email: str, password: str) -> tuple[bool, str]:  # Recibe datos del nuevo usuario y devuelve una tupla (éxito:bool, mensaje:str)
        """Crea un nuevo usuario. Devuelve (éxito, mensaje)."""
        try:                                                                        # Inicia manejo de errores para capturar violaciones de unicidad del email
            with self.conectar() as conn:                                           # Abre la conexión con commit/rollback automático
                conn.execute(                                                       # Ejecuta la sentencia SQL de inserción
                    "INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",  # Inserta el nuevo usuario; los "?" son marcadores de posición para prevenir SQL injection
                    (nombre, email, password),                                      # Tupla con los valores que sustituyen a los "?" en el mismo orden
                )
            return True, f"✅ Usuario '{nombre}' registrado con éxito."             # Si la inserción fue exitosa, devuelve True y un mensaje de confirmación
        except sqlite3.IntegrityError:                                              # Captura el error específico que SQLite lanza cuando se viola la restricción UNIQUE del email
            return False, "❌ El correo ya está registrado."                        # Devuelve False y un mensaje indicando que el email ya existe en la DB

    def verificar_login(self, email: str, password: str) -> tuple | None:           # Recibe credenciales y devuelve una tupla con datos del usuario o None si no coincide
        """Devuelve (id, nombre, saldo) si las credenciales son correctas, None si no."""
        with self.conectar() as conn:                                               # Abre la conexión a la DB
            return conn.execute(                                                    # Ejecuta la consulta y devuelve directamente el resultado (sin asignarlo a variable intermedia)
                "SELECT id, nombre, saldo FROM usuarios WHERE email = ? AND password = ?",  # Busca el usuario que coincida con ambos campos simultáneamente
                (email, password),                                                  # Tupla con los valores para sustituir los "?"
            ).fetchone()                                                            # fetchone() devuelve la primera fila encontrada como tupla, o None si no hay resultados

    # ─────────────────────────────────────────────────────────
    # PORTAFOLIO
    # ─────────────────────────────────────────────────────────

    def obtener_portafolio(self, usuario_id: int) -> dict:
        """
        Recupera el portafolio completo del usuario desde la DB.
        Devuelve: { "AAPL": {"cantidad": 10, "precio_compra_promedio": 195.30}, ... }
        """
        with self.conectar() as conn:                                               # Abre la conexión a la DB
            filas = conn.execute(                                                   # Ejecuta la consulta y guarda todas las filas resultantes en la variable filas
                "SELECT simbolo, cantidad, precio_compra_promedio FROM portafolio WHERE usuario_id = ?",  # Selecciona las 3 columnas relevantes filtrando por usuario
                (usuario_id,),                                                      # Tupla de un elemento con el ID del usuario (la coma es necesaria para que Python la reconozca como tupla)
            ).fetchall()                                                            # fetchall() devuelve todas las filas coincidentes como una lista de tuplas

        return {
            fila[0]: {                                                              # Usa el símbolo (primera columna) como clave del diccionario resultante
                "cantidad": fila[1],                                               # Mapea la segunda columna (cantidad de acciones) al campo "cantidad"
                "precio_compra_promedio": fila[2]                                  # Mapea la tercera columna al campo "precio_compra_promedio" (nombre vital para el resto de la app)
            } for fila in filas                                                     # Itera sobre cada fila del resultado para construir el diccionario completo
        }

    # ─────────────────────────────────────────────────────────
    # COMPRA
    # ─────────────────────────────────────────────────────────

    def guardar_compra(
        self,
        usuario_id: int,          # ID del usuario que realiza la compra
        simbolo: str,             # Ticker de la acción comprada
        cantidad_comprada: int,   # Número de acciones compradas en esta operación
        precio_compra: float,     # Precio unitario de la acción al momento de la compra
        nuevo_saldo: float,       # Saldo del usuario ya descontado el costo total de la compra
    ) -> bool:
        """
        Atomicamente: actualiza saldo, registra transacción y actualiza portafolio
        con precio promedio ponderado.
        """
        try:                                                        # Inicia manejo de errores para revertir cambios si alguna operación falla
            with self.conectar() as conn:                           # Abre la conexión; el context manager hace commit de todas las operaciones al salir, o rollback si hay error

                # 1. Actualizar saldo
                conn.execute(
                    "UPDATE usuarios SET saldo = ? WHERE id = ?",  # Modifica el saldo del usuario en la tabla usuarios
                    (nuevo_saldo, usuario_id),                      # Tupla con el nuevo saldo calculado externamente y el ID del usuario a actualizar
                )

                # Crea el objeto de zona horaria de Lima
                zona_peru = pytz.timezone('America/Lima')           # Instancia el objeto de zona horaria correspondiente a Perú (UTC-5)
                # Genera la fecha actual ajustada a esa zona
                fecha_actual = datetime.now(zona_peru).strftime("%Y-%m-%d %H:%M:%S")  # Obtiene la fecha y hora actual en Lima y la formatea como string legible

                # 2. Registrar transacción
                conn.execute(
                    "INSERT INTO transacciones (usuario_id, simbolo, cantidad, precio, tipo, fecha) "
                    "VALUES (?, ?, ?, ?, 'COMPRA', ?)",             # Inserta la transacción; el tipo 'COMPRA' va directamente en el SQL (valor fijo, no variable)
                    (usuario_id, simbolo, cantidad_comprada, precio_compra, fecha_actual),  # Tupla con los valores dinámicos de la operación
                )

                # 3. Actualizar portafolio (precio promedio ponderado)
                fila = conn.execute(
                    "SELECT cantidad, precio_compra_promedio FROM portafolio WHERE usuario_id = ? AND simbolo = ?",  # Busca si ya existe esta acción en el portafolio del usuario
                    (usuario_id, simbolo),                          # Filtra por ID de usuario y símbolo simultáneamente
                ).fetchone()                                        # fetchone() devuelve la fila existente o None si no hay posición previa

                if fila:                                            # Si ya existe una posición previa de este ticker, hay que actualizar con precio promedio ponderado
                    cant_actual, precio_anterior = fila             # Desempaqueta la fila en las variables de cantidad y precio promedio actuales
                    nueva_cantidad = cant_actual + cantidad_comprada  # Suma las acciones previas con las recién compradas para obtener el total
                    nuevo_promedio = (
                        (cant_actual * precio_anterior) + (cantidad_comprada * precio_compra)
                    ) / nueva_cantidad                              # Fórmula del precio promedio ponderado: (valor_anterior + valor_nuevo) / cantidad_total
                    conn.execute(
                        "UPDATE portafolio SET cantidad = ?, precio_compra_promedio = ? "
                        "WHERE usuario_id = ? AND simbolo = ?",     # Actualiza la fila existente en el portafolio con los nuevos valores
                        (nueva_cantidad, nuevo_promedio, usuario_id, simbolo),  # Tupla con los valores actualizados y las condiciones del WHERE
                    )
                else:                                               # Si no existe posición previa, es la primera compra de este ticker para el usuario
                    conn.execute(
                        "INSERT INTO portafolio (usuario_id, simbolo, cantidad, precio_compra_promedio) "
                        "VALUES (?, ?, ?, ?)",                      # Crea una nueva fila en el portafolio para este ticker
                        (usuario_id, simbolo, cantidad_comprada, precio_compra),  # El precio promedio inicial es simplemente el precio de esta primera compra
                    )
            return True                                             # Si todas las operaciones se completaron sin error, devuelve True indicando éxito
        except Exception as e:                                      # Captura cualquier excepción inesperada (errores de BD, restricciones, etc.)
            print(f"❌ Error al guardar compra: {e}")               # Imprime el mensaje de error en la consola para facilitar el diagnóstico
            return False                                            # Devuelve False indicando que la operación falló (el context manager habrá hecho rollback)

    # ─────────────────────────────────────────────────────────
    # VENTA
    # ─────────────────────────────────────────────────────────

    def guardar_venta(
        self,
        usuario_id: int,          # ID del usuario que realiza la venta
        simbolo: str,             # Ticker de la acción vendida
        cantidad_vendida: int,    # Número de acciones vendidas en esta operación
        precio_venta: float,      # Precio unitario de la acción al momento de la venta
        nuevo_saldo: float,       # Saldo del usuario ya sumado el ingreso total de la venta
    ) -> bool:
        """
        Atomicamente: actualiza saldo, registra transacción y reduce/elimina posición.
        """
        try:                                                        # Inicia manejo de errores para revertir cambios si alguna operación falla
            with self.conectar() as conn:                           # Abre la conexión; el context manager hace commit de todas las operaciones al salir, o rollback si hay error

                # 1. Actualizar saldo
                conn.execute(
                    "UPDATE usuarios SET saldo = ? WHERE id = ?",  # Modifica el saldo del usuario en la tabla usuarios con el nuevo valor ya calculado
                    (nuevo_saldo, usuario_id),                      # Tupla con el saldo actualizado y el ID del usuario
                )

                # Crea el objeto de zona horaria de Lima
                zona_peru = pytz.timezone('America/Lima')           # Instancia el objeto de zona horaria correspondiente a Perú (UTC-5)
                # Genera la fecha actual ajustada a esa zona
                fecha_actual = datetime.now(zona_peru).strftime("%Y-%m-%d %H:%M:%S")  # Obtiene la fecha y hora actual en Lima y la formatea como string legible

                # 2. Registrar transacción
                conn.execute(
                    "INSERT INTO transacciones (usuario_id, simbolo, cantidad, precio, tipo, fecha) "
                    "VALUES (?, ?, ?, ?, 'VENTA', ?)",              # Inserta la transacción; el tipo 'VENTA' va directamente en el SQL (valor fijo, no variable)
                    (usuario_id, simbolo, cantidad_vendida, precio_venta, fecha_actual),  # Tupla con los valores dinámicos de la operación de venta
                )

                # 3. Actualizar portafolio
                fila = conn.execute(
                    "SELECT cantidad FROM portafolio WHERE usuario_id = ? AND simbolo = ?",  # Consulta cuántas acciones tiene actualmente el usuario de ese ticker
                    (usuario_id, simbolo),                          # Filtra por ID de usuario y símbolo simultáneamente
                ).fetchone()                                        # fetchone() devuelve la fila con la cantidad actual o None si no existe posición

                if fila:                                            # Si existe una posición en el portafolio para ese ticker
                    cantidad_restante = fila[0] - cantidad_vendida  # Resta las acciones vendidas de las que tenía; fila[0] es la cantidad actual en la DB
                    if cantidad_restante <= 0:                      # Si no quedan acciones (o el resultado es negativo por algún error), elimina la posición completamente
                        conn.execute(
                            "DELETE FROM portafolio WHERE usuario_id = ? AND simbolo = ?",  # Elimina la fila del portafolio para ese ticker y usuario
                            (usuario_id, simbolo),                  # Condición del DELETE para apuntar exactamente al registro correcto
                        )
                    else:                                           # Si quedan acciones tras la venta parcial, actualiza la cantidad en el portafolio
                        conn.execute(
                            "UPDATE portafolio SET cantidad = ? WHERE usuario_id = ? AND simbolo = ?",  # Actualiza solo la cantidad; el precio promedio no cambia al vender
                            (cantidad_restante, usuario_id, simbolo),  # Tupla con la cantidad restante y las condiciones del WHERE
                        )
            return True                                             # Si todas las operaciones se completaron sin error, devuelve True indicando éxito
        except Exception as e:                                      # Captura cualquier excepción inesperada durante la operación
            print(f"❌ Error al guardar venta: {e}")                # Imprime el detalle del error en la consola para diagnóstico
            return False                                            # Devuelve False indicando que la operación falló (el context manager habrá hecho rollback)

    # ─────────────────────────────────────────────────────────
    # HISTORIAL
    # ─────────────────────────────────────────────────────────

    def obtener_historial(self, usuario_id: int) -> list[tuple]:    # Recibe el ID del usuario y devuelve una lista de tuplas con sus transacciones
        """
        Devuelve las transacciones del usuario ordenadas por fecha descendente.
        Cada fila: (simbolo, tipo, cantidad, precio, fecha)
        """
        with self.conectar() as conn:                               # Abre la conexión a la DB
            return conn.execute(
                "SELECT simbolo, tipo, cantidad, precio, fecha "
                "FROM transacciones WHERE usuario_id = ? ORDER BY fecha DESC",  # Filtra por usuario y ordena de más reciente a más antiguo (DESC = descendente)
                (usuario_id,),                                      # Tupla con el ID del usuario como único parámetro de filtro
            ).fetchall()                                            # fetchall() devuelve todas las filas coincidentes como una lista de tuplas; lista vacía si no hay historial
