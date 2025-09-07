from werkzeug.security import generate_password_hash
import mysql.connector

db_config = {
    'host': '127.0.0.1',
    'user': 'admin01',
    'password': 'MXR.2025',
    'database': 'MAXIRV7'
}


def registrar_usuario(usuario, password, permiso_validar=True):
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor()
    hash_pw = generate_password_hash(password)
    cur.execute(
        "INSERT INTO usuarios (usuario, password, permiso_validar) VALUES (%s, %s, %s)",
        (usuario, hash_pw, permiso_validar)
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"Usuario '{usuario}' creado correctamente.")


if __name__ == '__main__':
    usuario = input("Usuario: ")
    password = input("Contraseña: ")
    permiso = input("¿Puede validar empleados? (s/n): ").lower() == 's'
    registrar_usuario(usuario, password, permiso)
