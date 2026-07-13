"""
backend/database.py - TradeaYa!
Toda operación con la DB pasa por aquí: usuarios, portafolio y transacciones.

Modo LOCAL  → SQLite   (tradeaya.db)
Modo CLOUD  → PostgreSQL via Supabase (variable DATABASE_URL en Streamlit Secrets)

El método conectar() y el placeholder (?  vs  %s) se adaptan automáticamente.
"""

import os
import sqlite3
from datetime import datetime

import pytz


class DatabaseManager:
    """
    Gestiona la conexión y operaciones sobre la base de datos.
    Detecta automáticamente si debe usar SQLite (local) o PostgreSQL (Cloud).
    """

    def __init__(self, db_name: str = "tradeaya.db") -> None:
        self.db_name  = db_name
        self.db_url   = os.getenv("DATABASE_URL")  # Presente solo en Streamlit Cloud
        self.en_cloud = self.db_url is not None
        self._PH      = "%s" if self.en_cloud else "?"  # Placeholder SQL
        self._crear_tablas()

    # ─────────────────────────────────────────────────────────
    # CONEXIÓN UNIFICADA
    # ─────────────────────────────────────────────────────────

    def conectar(self):
        """
        Devuelve una conexión activa según el entorno:
          - Cloud : psycopg2 → PostgreSQL (Supabase)
          - Local : sqlite3  → archivo .db
        """
        if self.en_cloud:
            import psycopg2
            return psycopg2.connect(self.db_url)
        return sqlite3.connect(self.db_name, timeout=10)

    def _ejecutar(self, conn, sql: str, params: tuple = ()):
        """
        Ejecuta una query adaptando los placeholders al motor activo.
        En SQLite usa '?', en PostgreSQL usa '%s'.
        Devuelve el cursor para fetchone/fetchall.
        """
        sql_adaptado = sql.replace("?", self._PH)
        cur = conn.cursor()
        cur.execute(sql_adaptado, params)
        return cur

    # ─────────────────────────────────────────────────────────
    # UTILIDAD INTERNA
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _timestamp_ny() -> str:
        """Devuelve la fecha/hora actual en zona horaria de Nueva York como string."""
        return datetime.now(pytz.timezone("America/New_York")).strftime("%Y-%m-%d %H:%M:%S")

    # ─────────────────────────────────────────────────────────
    # INICIALIZACIÓN DE TABLAS
    # ─────────────────────────────────────────────────────────

    def _crear_tablas(self) -> None:
        """Crea las tablas si no existen. Se llama una sola vez al iniciar."""
        with self.conectar() as conn:
            if self.en_cloud:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id       SERIAL PRIMARY KEY,
                        nombre   TEXT   NOT NULL,
                        email    TEXT   UNIQUE NOT NULL,
                        password TEXT   NOT NULL,
                        saldo    REAL   DEFAULT 10000.0
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS transacciones (
                        id         SERIAL PRIMARY KEY,
                        usuario_id INTEGER NOT NULL,
                        simbolo    TEXT    NOT NULL,
                        cantidad   INTEGER NOT NULL,
                        precio     REAL    NOT NULL,
                        tipo       TEXT    NOT NULL,
                        fecha      TEXT    NOT NULL
                    )
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS portafolio (
                        id                     SERIAL PRIMARY KEY,
                        usuario_id             INTEGER NOT NULL,
                        simbolo                TEXT    NOT NULL,
                        cantidad               INTEGER NOT NULL,
                        precio_compra_promedio REAL    NOT NULL,
                        UNIQUE(usuario_id, simbolo)
                    )
                """)
                conn.commit()
            else:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id       INTEGER PRIMARY KEY AUTOINCREMENT,
                        nombre   TEXT    NOT NULL,
                        email    TEXT    UNIQUE NOT NULL,
                        password TEXT    NOT NULL,
                        saldo    REAL    DEFAULT 10000.0
                    );
                    CREATE TABLE IF NOT EXISTS transacciones (
                        id         INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id INTEGER NOT NULL,
                        simbolo    TEXT    NOT NULL,
                        cantidad   INTEGER NOT NULL,
                        precio     REAL    NOT NULL,
                        tipo       TEXT    NOT NULL,
                        fecha      TEXT    NOT NULL
                    );
                    CREATE TABLE IF NOT EXISTS portafolio (
                        id                     INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id             INTEGER,
                        simbolo                TEXT    NOT NULL,
                        cantidad               INTEGER NOT NULL,
                        precio_compra_promedio REAL    NOT NULL,
                        FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
                        UNIQUE(usuario_id, simbolo)
                    );
                """)

    # ─────────────────────────────────────────────────────────
    # USUARIOS
    # ─────────────────────────────────────────────────────────

    def registrar_usuario(self, nombre: str, email: str, password: str) -> tuple[bool, str]:
        """Crea un nuevo usuario. Devuelve (éxito, mensaje)."""
        try:
            with self.conectar() as conn:
                self._ejecutar(
                    conn,
                    "INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",
                    (nombre, email, password),
                )
                if self.en_cloud:
                    conn.commit()
            return True, f"✅ Usuario '{nombre}' registrado con éxito."
        except Exception as e:
            err = str(e).lower()
            if "unique" in err or "duplicate" in err:
                return False, "❌ El correo ya está registrado."
            return False, f"❌ Error al registrar: {e}"

    def verificar_login(self, email: str, password: str) -> tuple | None:
        """Devuelve (id, nombre, saldo) si las credenciales son correctas, None si no."""
        with self.conectar() as conn:
            cur = self._ejecutar(
                conn,
                "SELECT id, nombre, saldo FROM usuarios WHERE email = ? AND password = ?",
                (email, password),
            )
            return cur.fetchone()

    # ─────────────────────────────────────────────────────────
    # PORTAFOLIO
    # ─────────────────────────────────────────────────────────

    def obtener_portafolio(self, usuario_id: int) -> dict:
        """
        Recupera el portafolio completo del usuario desde la DB.
        Devuelve: { "AAPL": {"cantidad": 10, "precio_compra_promedio": 195.30}, ... }
        """
        with self.conectar() as conn:
            cur = self._ejecutar(
                conn,
                "SELECT simbolo, cantidad, precio_compra_promedio "
                "FROM portafolio WHERE usuario_id = ?",
                (usuario_id,),
            )
            filas = cur.fetchall()

        return {
            fila[0]: {"cantidad": fila[1], "precio_compra_promedio": fila[2]}
            for fila in filas
        }

    # ─────────────────────────────────────────────────────────
    # COMPRA
    # ─────────────────────────────────────────────────────────

    def guardar_compra(
        self,
        usuario_id: int,
        simbolo: str,
        cantidad_comprada: int,
        precio_compra: float,
        nuevo_saldo: float,
    ) -> bool:
        """Actualiza saldo, registra transacción y actualiza portafolio."""
        try:
            with self.conectar() as conn:
                self._ejecutar(
                    conn,
                    "UPDATE usuarios SET saldo = ? WHERE id = ?",
                    (nuevo_saldo, usuario_id),
                )
                self._ejecutar(
                    conn,
                    "INSERT INTO transacciones "
                    "(usuario_id, simbolo, cantidad, precio, tipo, fecha) "
                    "VALUES (?, ?, ?, ?, 'COMPRA', ?)",
                    (usuario_id, simbolo, cantidad_comprada,
                     precio_compra, self._timestamp_ny()),
                )
                cur = self._ejecutar(
                    conn,
                    "SELECT cantidad, precio_compra_promedio "
                    "FROM portafolio WHERE usuario_id = ? AND simbolo = ?",
                    (usuario_id, simbolo),
                )
                fila = cur.fetchone()
                if fila:
                    cant_actual, precio_anterior = fila
                    nueva_cantidad = cant_actual + cantidad_comprada
                    nuevo_promedio = (
                        (cant_actual * precio_anterior)
                        + (cantidad_comprada * precio_compra)
                    ) / nueva_cantidad
                    self._ejecutar(
                        conn,
                        "UPDATE portafolio "
                        "SET cantidad = ?, precio_compra_promedio = ? "
                        "WHERE usuario_id = ? AND simbolo = ?",
                        (nueva_cantidad, nuevo_promedio, usuario_id, simbolo),
                    )
                else:
                    self._ejecutar(
                        conn,
                        "INSERT INTO portafolio "
                        "(usuario_id, simbolo, cantidad, precio_compra_promedio) "
                        "VALUES (?, ?, ?, ?)",
                        (usuario_id, simbolo, cantidad_comprada, precio_compra),
                    )
                if self.en_cloud:
                    conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al guardar compra: {e}")
            return False

    # ─────────────────────────────────────────────────────────
    # VENTA
    # ─────────────────────────────────────────────────────────

    def guardar_venta(
        self,
        usuario_id: int,
        simbolo: str,
        cantidad_vendida: int,
        precio_venta: float,
        nuevo_saldo: float,
    ) -> bool:
        """Actualiza saldo, registra transacción y reduce/elimina posición."""
        try:
            with self.conectar() as conn:
                self._ejecutar(
                    conn,
                    "UPDATE usuarios SET saldo = ? WHERE id = ?",
                    (nuevo_saldo, usuario_id),
                )
                self._ejecutar(
                    conn,
                    "INSERT INTO transacciones "
                    "(usuario_id, simbolo, cantidad, precio, tipo, fecha) "
                    "VALUES (?, ?, ?, ?, 'VENTA', ?)",
                    (usuario_id, simbolo, cantidad_vendida,
                     precio_venta, self._timestamp_ny()),
                )
                cur = self._ejecutar(
                    conn,
                    "SELECT cantidad FROM portafolio "
                    "WHERE usuario_id = ? AND simbolo = ?",
                    (usuario_id, simbolo),
                )
                fila = cur.fetchone()
                if fila:
                    cantidad_restante = fila[0] - cantidad_vendida
                    if cantidad_restante <= 0:
                        self._ejecutar(
                            conn,
                            "DELETE FROM portafolio "
                            "WHERE usuario_id = ? AND simbolo = ?",
                            (usuario_id, simbolo),
                        )
                    else:
                        self._ejecutar(
                            conn,
                            "UPDATE portafolio SET cantidad = ? "
                            "WHERE usuario_id = ? AND simbolo = ?",
                            (cantidad_restante, usuario_id, simbolo),
                        )
                if self.en_cloud:
                    conn.commit()
            return True
        except Exception as e:
            print(f"❌ Error al guardar venta: {e}")
            return False

    # ─────────────────────────────────────────────────────────
    # HISTORIAL
    # ─────────────────────────────────────────────────────────

    def obtener_historial(self, usuario_id: int) -> list[tuple]:
        """
        Devuelve las transacciones del usuario ordenadas por fecha descendente.
        Cada fila: (simbolo, tipo, cantidad, precio, fecha)
        """
        with self.conectar() as conn:
            cur = self._ejecutar(
                conn,
                "SELECT simbolo, tipo, cantidad, precio, fecha "
                "FROM transacciones WHERE usuario_id = ? ORDER BY fecha DESC",
                (usuario_id,),
            )
            return cur.fetchall()
