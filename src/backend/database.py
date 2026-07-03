"""
backend/database.py - TradeaYa!
Capa de acceso a datos: usuarios, portafolio y transacciones.
Toda operación con SQLite pasa por aquí.
"""

import os
import sqlite3
from datetime import datetime
import pytz


class DatabaseManager:
    """Gestiona la conexión y operaciones sobre la base de datos SQLite."""

    def __init__(self, db_name: str = "tradeaya.db") -> None:
        self.db_url = os.getenv("DATABASE_URL") # Supabase en Cloud
        self.db_name = db_name # SQLite en Local
        self._crear_tablas()

    # ─────────────────────────────────────────────────────────
    # CONEXIÓN
    # ─────────────────────────────────────────────────────────

    def conectar(self) -> sqlite3.Connection:
        """Devuelve una conexión con timeout para evitar 'database is locked'."""
         if self.db_url:                                   # Si hay Cloud → PostgreSQL
             import psycopg2
             return psycopg2.connect(self.db_url)
        return sqlite3.connect(self.db_name, timeout=10) # Si no hay Cloud → SQLite nomás

    # ─────────────────────────────────────────────────────────
    # UTILIDAD INTERNA
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _timestamp_lima() -> str:
        """Devuelve la fecha/hora actual en zona horaria de Lima como string."""
        return datetime.now(pytz.timezone("America/Lima")).strftime("%Y-%m-%d %H:%M:%S")

    # ─────────────────────────────────────────────────────────
    # INICIALIZACIÓN DE TABLAS
    # ─────────────────────────────────────────────────────────

    def _crear_tablas(self) -> None:
        """Crea las tablas si no existen. Se llama una sola vez al iniciar."""
        with self.conectar() as conn:
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
                conn.execute(
                    "INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)",
                    (nombre, email, password),
                )
            return True, f"✅ Usuario '{nombre}' registrado con éxito."
        except sqlite3.IntegrityError:
            return False, "❌ El correo ya está registrado."

    def verificar_login(self, email: str, password: str) -> tuple | None:
        """Devuelve (id, nombre, saldo) si las credenciales son correctas, None si no."""
        with self.conectar() as conn:
            return conn.execute(
                "SELECT id, nombre, saldo FROM usuarios WHERE email = ? AND password = ?",
                (email, password),
            ).fetchone()

    # ─────────────────────────────────────────────────────────
    # PORTAFOLIO
    # ─────────────────────────────────────────────────────────

    def obtener_portafolio(self, usuario_id: int) -> dict:
        """
        Recupera el portafolio completo del usuario desde la DB.
        Devuelve: { "AAPL": {"cantidad": 10, "precio_compra_promedio": 195.30}, ... }
        """
        with self.conectar() as conn:
            filas = conn.execute(
                "SELECT simbolo, cantidad, precio_compra_promedio FROM portafolio WHERE usuario_id = ?",
                (usuario_id,),
            ).fetchall()

        return {
            fila[0]: {
                "cantidad": fila[1],
                "precio_compra_promedio": fila[2],
            }
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
        """Atómicamente: actualiza saldo, registra transacción y actualiza portafolio."""
        try:
            with self.conectar() as conn:
                conn.execute(
                    "UPDATE usuarios SET saldo = ? WHERE id = ?",
                    (nuevo_saldo, usuario_id),
                )
                conn.execute(
                    "INSERT INTO transacciones (usuario_id, simbolo, cantidad, precio, tipo, fecha) "
                    "VALUES (?, ?, ?, ?, 'COMPRA', ?)",
                    (usuario_id, simbolo, cantidad_comprada, precio_compra, self._timestamp_lima()),
                )

                fila = conn.execute(
                    "SELECT cantidad, precio_compra_promedio FROM portafolio WHERE usuario_id = ? AND simbolo = ?",
                    (usuario_id, simbolo),
                ).fetchone()

                if fila:
                    cant_actual, precio_anterior = fila
                    nueva_cantidad = cant_actual + cantidad_comprada
                    nuevo_promedio = (
                        (cant_actual * precio_anterior) + (cantidad_comprada * precio_compra)
                    ) / nueva_cantidad
                    conn.execute(
                        "UPDATE portafolio SET cantidad = ?, precio_compra_promedio = ? "
                        "WHERE usuario_id = ? AND simbolo = ?",
                        (nueva_cantidad, nuevo_promedio, usuario_id, simbolo),
                    )
                else:
                    conn.execute(
                        "INSERT INTO portafolio (usuario_id, simbolo, cantidad, precio_compra_promedio) "
                        "VALUES (?, ?, ?, ?)",
                        (usuario_id, simbolo, cantidad_comprada, precio_compra),
                    )
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
        """Atómicamente: actualiza saldo, registra transacción y reduce/elimina posición."""
        try:
            with self.conectar() as conn:
                conn.execute(
                    "UPDATE usuarios SET saldo = ? WHERE id = ?",
                    (nuevo_saldo, usuario_id),
                )
                conn.execute(
                    "INSERT INTO transacciones (usuario_id, simbolo, cantidad, precio, tipo, fecha) "
                    "VALUES (?, ?, ?, ?, 'VENTA', ?)",
                    (usuario_id, simbolo, cantidad_vendida, precio_venta, self._timestamp_lima()),
                )

                fila = conn.execute(
                    "SELECT cantidad FROM portafolio WHERE usuario_id = ? AND simbolo = ?",
                    (usuario_id, simbolo),
                ).fetchone()

                if fila:
                    cantidad_restante = fila[0] - cantidad_vendida
                    if cantidad_restante <= 0:
                        conn.execute(
                            "DELETE FROM portafolio WHERE usuario_id = ? AND simbolo = ?",
                            (usuario_id, simbolo),
                        )
                    else:
                        conn.execute(
                            "UPDATE portafolio SET cantidad = ? WHERE usuario_id = ? AND simbolo = ?",
                            (cantidad_restante, usuario_id, simbolo),
                        )
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
            return conn.execute(
                "SELECT simbolo, tipo, cantidad, precio, fecha "
                "FROM transacciones WHERE usuario_id = ? ORDER BY fecha DESC",
                (usuario_id,),
            ).fetchall()
