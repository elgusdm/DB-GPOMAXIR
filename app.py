from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import timedelta
import mysql.connector
import barcode
from barcode.writer import ImageWriter
import os
from werkzeug.security import check_password_hash, generate_password_hash
from mysql.connector.errors import IntegrityError
from email_utils import fill_word_template, send_email_with_attachment
from flask_mail import Mail

app = Flask(__name__)
# Clave segura en producción
app.secret_key = 'tu_clave_secreta'
# Duración de la sesión si "recordarme" está activo
app.permanent_session_lifetime = timedelta(days=7)

# Configuración de la conexión a la base de datos
db_config = {
    'host': '127.0.0.1',
    'user': 'admin01',
    'password': 'MXR.2025',
    'database': 'MAXIRV7'
}

# Configuración de Flask-Mail (ajusta con tus datos reales)
app.config['MAIL_SERVER'] = 'smtp.tu-servidor.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tu_usuario@dominio.com'
app.config['MAIL_PASSWORD'] = 'tu_contraseña'
mail = Mail(app)

# Función para generar el código de barras


def generar_barcode(empleado_id):
    carpeta = 'barcodes'
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    filename = os.path.join(carpeta, f'empleado_{empleado_id}.png')
    codigo = barcode.get('code128', str(empleado_id), writer=ImageWriter())
    codigo.save(filename)
    return filename

# Rutas

# ruta raiz


@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/home')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('home.html')

# ruta del login


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        # Checkbox: 'on' si está marcado
        recordarme = request.form.get('recordarme')
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM usuarios WHERE usuario = %s", (usuario,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user['password'], password):
            if user['permiso_validar']:
                session['usuario'] = usuario
                if recordarme:
                    session.permanent = True
                else:
                    session.permanent = False
                return redirect(url_for('home'))
            else:
                flash('No tienes permiso para validar empleados.', 'error')
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

# ruta del formulario de validación


@app.route('/validar_form', methods=['GET'])
def validar_form():
    if 'usuario' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'error')
        return redirect(url_for('login'))
    return render_template('validar_form.html')

# ruta de registro


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


# Ruta para enviar email
@app.route('/email', methods=['GET'])
def email():
    conn = mysql.connector.connect(**db_config)
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, nombre, puesto FROM empleados")
    empleados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('email.html', empleados=empleados)


@app.route('/enviar_email', methods=['POST'])
def enviar_email():
    destinatario = request.form.get('destinatario')
    if not destinatario:
        flash('Debes ingresar un correo válido.', 'error')
        return redirect(url_for('email'))
    # Simula datos de la base de datos
    datos = {
        'nombre': 'Juan Pérez',
        'fecha': '2025-09-19',
        'proyecto': 'Ejemplo',
    }
    # Debes crear este archivo con {{nombre}}, {{fecha}}, etc.
    template_path = 'static/plantillas/formato.docx'
    output_path = 'static/plantillas/formato_relleno.docx'
    fill_word_template(template_path, output_path, datos)
    subject = 'Documento generado'
    recipients = [destinatario]
    body = 'Adjunto el documento solicitado.'
    send_email_with_attachment(mail, subject, recipients, body, output_path)
    flash('Correo enviado correctamente.', 'success')
    return redirect(url_for('email'))

# Ruta para validar empleado por código de barras


@app.route('/validar', methods=['POST'])
def validar():
    if 'usuario' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'error')
        return redirect(url_for('login'))
    empleado_id = request.form.get('empleado_id')
    if not empleado_id:
        flash('ID de empleado requerido.')
        return redirect(url_for('validar_form'))
    try:
        conn = mysql.connector.connect(**db_config)
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM empleados WHERE id = %s", (empleado_id,))
        empleado = cur.fetchone()
        if not empleado:
            cur.close()
            conn.close()
            flash('Empleado no encontrado.')
            return redirect(url_for('validar_form'))
        if empleado.get('validado'):
            mensaje = 'El empleado ya fue validado.'
        else:
            # Marca como validado
            cur.execute(
                "UPDATE empleados SET validado = TRUE WHERE id = %s", (empleado_id,))
            conn.commit()
            mensaje = 'Empleado validado exitosamente.'
        cur.close()
        conn.close()
        return render_template('validacion.html', empleado=empleado, mensaje=mensaje)
    except Exception as e:
        flash(f'Error en la validación: {e}')
        return redirect(url_for('validar_form'))

# Ruta para registrar nuevos usuarios


@app.route('/registro_usuario', methods=['POST'])
def registro_usuario():
    usuario = request.form.get('usuario')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    permiso_validar = True if request.form.get('permiso_validar') else False

    if not usuario or not password or not password2:
        flash('Todos los campos son requeridos.')
        return redirect(url_for('registro'))

    if password != password2:
        flash('Las contraseñas no coinciden.')
        return redirect(url_for('registro'))

    try:
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
        flash('Usuario registrado correctamente.')
        return redirect(url_for('login'))
    except IntegrityError:
        flash('El usuario ya existe. Elige otro nombre de usuario.')
        return redirect(url_for('registro'))
    except Exception as e:
        flash(f'Error al registrar usuario: {e}')
        return redirect(url_for('registro'))


@app.route('/enviar_email_demo')
def enviar_email_demo():
    # Simula datos de la base de datos
    datos = {
        'nombre': 'Juan Pérez',
        'fecha': '2025-09-19',
        'proyecto': 'Ejemplo',
    }
    # Debes crear este archivo con {{nombre}}, {{fecha}}, etc.
    template_path = 'static/plantillas/formato.docx'
    output_path = 'static/plantillas/formato_relleno.docx'
    fill_word_template(template_path, output_path, datos)
    subject = 'Documento generado'
    recipients = ['cliente@ejemplo.com']
    body = 'Adjunto el documento solicitado.'
    send_email_with_attachment(mail, subject, recipients, body, output_path)
    return 'Correo enviado con adjunto.'

# Medidas de seguridad:
# - Parámetros en SQL para evitar inyección.
# - App.secret_key por una clave segura.
# - HTTPS en producción.
# - Limitar permisos del usuario de la base de datos.
# - Validar y sanitizar todas las entradas del usuario.


if __name__ == '__main__':
    app.run(debug=True)
