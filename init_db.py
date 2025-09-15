import sqlite3
from werkzeug.security import generate_password_hash

def init_database():
    conn = sqlite3.connect('maxir.db')
    cursor = conn.cursor()
    
    # Crear tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            permiso_validar BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Crear tabla de empleados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            puesto TEXT NOT NULL,
            validado BOOLEAN DEFAULT FALSE
        )
    ''')
    
    # Crear usuario administrador por defecto
    admin_password = generate_password_hash('admin123')
    cursor.execute('''
        INSERT OR IGNORE INTO usuarios (usuario, password, permiso_validar)
        VALUES (?, ?, ?)
    ''', ('admin', admin_password, True))
    
    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente")

if __name__ == '__main__':
    init_database()