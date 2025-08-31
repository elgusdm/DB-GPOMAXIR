from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
import barcode
from barcode.writer import ImageWriter
import os

app = Flask(__name__)
# Cambia esto por una clave segura en producción
app.secret_key = 'tu_clave_secreta'

# Configuración de la conexión a la base de datos (adapta estos valores cuando tengas la base creada)
db_config = {
    'host': 'localhost',
    'user': 'tu_usuario',
    'password': 'tu_contraseña',
    'database': 'tu_base_de_datos'
}

# Función para generar el código de barras


def generar_barcode(empleado_id):
    carpeta = 'static/barcodes'
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    filename = os.path.join(carpeta, f'empleado_{empleado_id}.png')
    codigo = barcode.get('code128', str(empleado_id), writer=ImageWriter())
    codigo.save(filename)
    return filename

# Ruta para mostrar formulario de registro


@app.route('/registro')
def registro():
    return render_template('registro.html')

# Ruta para registrar empleado


@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = request.form.get('nombre')
    puesto = request.form.get('puesto')
    if not nombre or not puesto:
        flash('Nombre y puesto son requeridos.')
        return redirect(url_for('registro'))
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO empleados (nombre, puesto) VALUES (%s, %s)", (nombre, puesto))
        conn.commit()
        empleado_id = cur.lastrowid
        cur.close()
        conn.close()
        generar_barcode(empleado_id)
        flash('Empleado registrado correctamente.')
        return render_template('credencial.html', empleado_id=empleado_id, nombre=nombre, puesto=puesto)
    except Exception as e:
        flash(f'Error al registrar: {e}')
        return redirect(url_for('registro'))

# Ruta para validar empleado por código de barras


@app.route('/validar', methods=['POST'])
def validar():
    empleado_id = request.form.get('empleado_id')
    if not empleado_id:
        flash('ID de empleado requerido.')
        return redirect(url_for('login'))
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM empleados WHERE id = %s", (empleado_id,))
        empleado = cur.fetchone()
        cur.close()
        conn.close()
        if empleado:
            return render_template('validacion.html', empleado=empleado)
        else:
            flash('Empleado no encontrado.')
            return redirect(url_for('login'))
    except Exception as e:
        flash(f'Error en la validación: {e}')
        return redirect(url_for('login'))

# Medidas de seguridad:
# - Usa parámetros en SQL para evitar inyección.
# - Cambia app.secret_key por una clave segura.
# - Usa HTTPS en producción.
# - Limita permisos del usuario de la base de datos.
# - Valida y sanitiza todas las entradas del usuario.


if __name__ == '__main__':
    app.run(debug=True)
