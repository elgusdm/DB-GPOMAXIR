from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import timedelta
import sqlite3
import barcode
from barcode.writer import ImageWriter
import os
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_muy_segura_2025'
app.permanent_session_lifetime = timedelta(days=7)

# Configuración de la base de datos SQLite
DATABASE = 'maxir.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def generar_barcode(empleado_id):
    carpeta = 'static/barcodes'
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
    filename = os.path.join(carpeta, f'empleado_{empleado_id}.png')
    codigo = barcode.get('code128', str(empleado_id), writer=ImageWriter())
    codigo.save(filename)
    return filename

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        password = request.form.get('password')
        recordarme = request.form.get('recordarme')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE usuario = ?', (usuario,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            if user['permiso_validar']:
                session['usuario'] = usuario
                if recordarme:
                    session.permanent = True
                else:
                    session.permanent = False
                return redirect(url_for('validar_form'))
            else:
                flash('No tienes permiso para validar empleados.', 'error')
        else:
            flash('Usuario o contraseña incorrectos.', 'error')
    return render_template('login.html')

@app.route('/validar_form', methods=['GET'])
def validar_form():
    if 'usuario' not in session:
        flash('Debes iniciar sesión para acceder a esta página.', 'error')
        return redirect(url_for('login'))
    return render_template('validar_form.html')

@app.route('/registro')
def registro():
    return render_template('registro.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    nombre = request.form.get('nombre')
    puesto = request.form.get('puesto')
    if not nombre or not puesto:
        flash('Nombre y puesto son requeridos.')
        return redirect(url_for('registro'))
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO empleados (nombre, puesto) VALUES (?, ?)', (nombre, puesto))
        empleado_id = cursor.lastrowid
        conn.commit()
        conn.close()
        generar_barcode(empleado_id)
        flash('Empleado registrado correctamente.')
        return render_template('credencial.html', empleado_id=empleado_id, nombre=nombre, puesto=puesto)
    except Exception as e:
        flash(f'Error al registrar: {e}')
        return redirect(url_for('registro'))

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
        conn = get_db_connection()
        empleado = conn.execute('SELECT * FROM empleados WHERE id = ?', (empleado_id,)).fetchone()
        if not empleado:
            conn.close()
            flash('Empleado no encontrado.')
            return redirect(url_for('validar_form'))
        if empleado['validado']:
            mensaje = 'El empleado ya fue validado.'
        else:
            conn.execute('UPDATE empleados SET validado = 1 WHERE id = ?', (empleado_id,))
            conn.commit()
            mensaje = 'Empleado validado exitosamente.'
        conn.close()
        return render_template('validacion.html', empleado=empleado, mensaje=mensaje)
    except Exception as e:
        flash(f'Error en la validación: {e}')
        return redirect(url_for('validar_form'))

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
        conn = get_db_connection()
        hash_pw = generate_password_hash(password)
        conn.execute(
            'INSERT INTO usuarios (usuario, password, permiso_validar) VALUES (?, ?, ?)',
            (usuario, hash_pw, permiso_validar)
        )
        conn.commit()
        conn.close()
        flash('Usuario registrado correctamente.')
        return redirect(url_for('login'))
    except sqlite3.IntegrityError:
        flash('El usuario ya existe. Elige otro nombre de usuario.')
        return redirect(url_for('registro'))
    except Exception as e:
        flash(f'Error al registrar usuario: {e}')
        return redirect(url_for('registro'))

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    flash('Has cerrado sesión correctamente.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)