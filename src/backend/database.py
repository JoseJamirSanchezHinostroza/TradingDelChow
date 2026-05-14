import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_name="tradeaya.db"):
        self.db_name = db_name
        self.crear_tablas()

    def conectar(self):
        # Timeout para evitar el error 'database is locked'
        return sqlite3.connect(self.db_name, timeout=10)

    def crear_tablas(self):
        """Crea la estructura necesaria para usuarios y sus activos."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            # Tabla de Usuarios con Contraseña
            cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT UNIQUE, 
                 password TEXT, saldo REAL DEFAULT 100000.0)''')
            
            # Tabla de Transacciones (Historial)
            cursor.execute('''CREATE TABLE IF NOT EXISTS transacciones 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, simbolo TEXT, 
                cantidad INTEGER, precio REAL, tipo TEXT, fecha TEXT)''')
            
            # Tabla de Portafolio (Lo que posee cada uno)
            cursor.execute('''CREATE TABLE IF NOT EXISTS portafolio 
                (usuario_id INTEGER, simbolo TEXT, cantidad INTEGER, 
                PRIMARY KEY(usuario_id, simbolo))''')
            conn.commit()

    def registrar_usuario(self, nombre, email, password):
        try:
            with self.conectar() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)', 
                               (nombre, email, password))
                conn.commit()
            return True, f"✅ Usuario {nombre} registrado con éxito."
        except sqlite3.IntegrityError:
            return False, "❌ El correo ya está registrado."

    def verificar_login(self, email, password):
        """Devuelve los datos del usuario si las credenciales coinciden."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            return cursor.execute("SELECT id, nombre, saldo FROM usuarios WHERE email=? AND password=?", 
                                  (email, password)).fetchone()

    def actualizar_saldo_y_compra(self, usuario_id, simbolo, cantidad, precio, nuevo_saldo):
        """Registra la compra y descuenta el saldo en una sola operación segura."""
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.conectar() as conn:
                cursor = conn.cursor()
                # 1. Descontar Saldo
                cursor.execute("UPDATE usuarios SET saldo = ? WHERE id = ?", (nuevo_saldo, usuario_id))
                # 2. Registrar en Historial
                cursor.execute("INSERT INTO transacciones (usuario_id, simbolo, cantidad, precio, tipo, fecha) VALUES (?,?,?,?,'COMPRA',?)",
                               (usuario_id, simbolo, cantidad, precio, fecha))
                # 3. Añadir al Portafolio
                cursor.execute("INSERT INTO portafolio (usuario_id, simbolo, cantidad) VALUES (?,?,?) ON CONFLICT(usuario_id, simbolo) DO UPDATE SET cantidad = cantidad + ?", 
                               (usuario_id, simbolo, cantidad, cantidad))
                conn.commit()
            return True
        except Exception as e:
            print(f"Error en DB: {e}")
            return False

    def obtener_portafolio(self, usuario_id):
        """Recupera todas las acciones que posee un usuario con la estructura correcta."""
        with self.conectar() as conn:
            cursor = conn.cursor()
            # Traemos todos los datos de la tabla portafolio
            cursor.execute("SELECT * FROM portafolio WHERE usuario_id = ?", (usuario_id,))
            filas = cursor.fetchall()
            
            # Obtenemos los nombres de las columnas para evitar errores
            columnas = [descripcion[0] for descripcion in cursor.description]
            
            portafolio_armado = {}
            for fila in filas:
                # Convertimos la fila en un diccionario fácil de leer
                datos_fila = dict(zip(columnas, fila))
                
                simbolo = datos_fila.get('simbolo')
                cantidad = datos_fila.get('cantidad', 0)
                
                # Buscamos la columna del precio (por si tu compañero la llamó distinto)
                precio_prom = datos_fila.get('precio_compra_promedio', 
                              datos_fila.get('precio_compra', 
                              datos_fila.get('precio', 0.0)))
                
                # Armamos el diccionario EXACTAMENTE como lo espera sesion.py
                portafolio_armado[simbolo] = {
                    "cantidad": cantidad,
                    "precio_compra_promedio": precio_prom
                }
                
            return portafolio_armado
