"""
Servidor API REST - PFO2 Programación sobre Redes
Desarrollado con Flask y SQLite
"""

import sqlite3
import os
from flask import Flask, request, jsonify, render_template_string, redirect
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
DB_NAME = "pfo2_tareas.db"

# ==========================================
# GESTIÓN DE BASE DE DATOS (SQLite)
# ==========================================

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos y crea las tablas necesarias si no existen."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Tabla de Tareas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            completada INTEGER DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# ==========================================
# ENDPOINTS DE LA API REST Y VISTAS HTML
# ==========================================

@app.route('/', methods=['GET'])
def index():
    if 'text/html' in request.headers.get('Accept', ''):
        return redirect('/tareas')
    return jsonify({
        "mensaje": "Bienvenido a la API REST de Gestión de Tareas - PFO2",
        "endpoints": {
            "POST /registro": "Registrar nuevo usuario",
            "POST /login": "Iniciar sesión y verificar credenciales",
            "GET /tareas": "Listar tareas (vista HTML en navegador o JSON para cliente)",
            "POST /tareas": "Crear nueva tarea",
            "PUT /tareas/<id>": "Marcar tarea como completada",
            "DELETE /tareas/<id>": "Eliminar tarea"
        }
    }), 200

@app.route('/registro', methods=['POST'])
def registro():
    """Endpoint para registrar un nuevo usuario con contraseña hasheada."""
    if request.is_json:
        data = request.get_json() or {}
        usuario = data.get('usuario')
        password = data.get('contraseña') or data.get('password')
    else:
        usuario = request.form.get('usuario')
        password = request.form.get('contraseña') or request.form.get('password')

    if not usuario or not password:
        return jsonify({"error": "Se requieren los campos 'usuario' y 'contraseña'."}), 400

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
            (usuario, hashed_password)
        )
        conn.commit()
        if not request.is_json and 'text/html' in request.headers.get('Accept', ''):
            return redirect('/tareas')
        return jsonify({"mensaje": f"Usuario '{usuario}' registrado con éxito."}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"El usuario '{usuario}' ya existe."}), 409
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    """Endpoint para autenticar usuarios mediante verificación de hash."""
    if request.is_json:
        data = request.get_json() or {}
        usuario = data.get('usuario')
        password = data.get('contraseña') or data.get('password')
    else:
        usuario = request.form.get('usuario')
        password = request.form.get('contraseña') or request.form.get('password')

    if not usuario or not password:
        return jsonify({"error": "Se requieren 'usuario' y 'contraseña'."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM usuarios WHERE usuario = ?", (usuario,))
    user_row = cursor.fetchone()
    conn.close()

    if user_row and check_password_hash(user_row['password_hash'], password):
        return jsonify({
            "mensaje": "Inicio de sesión exitoso.",
            "usuario_id": user_row['id'],
            "usuario": user_row['usuario']
        }), 200
    else:
        return jsonify({"error": "Credenciales inválidas (usuario o contraseña incorrectos)."}), 401

@app.route('/tareas', methods=['GET'])
def obtener_tareas():
    """Devuelve vista HTML estilizada en navegador web o JSON para cliente CLI."""
    usuario = request.args.get('usuario')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Si la petición proviene de un navegador web (text/html) y no viene con parametro exclusivo
    if 'text/html' in request.headers.get('Accept', '') and not usuario:
        cursor.execute("""
            SELECT t.id, t.titulo, t.completada, u.usuario 
            FROM tareas t 
            JOIN usuarios u ON t.usuario_id = u.id
            ORDER BY t.id DESC
        """)
        tareas_rows = [dict(row) for row in cursor.fetchall()]

        cursor.execute("SELECT id, usuario FROM usuarios ORDER BY id ASC")
        usuarios_rows = [dict(row) for row in cursor.fetchall()]
        conn.close()

        html_content = """
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PFO2 - Registro de Tareas y Usuarios</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #eef2f5; margin: 0; padding: 30px; color: #333; }
                .container { max-width: 900px; margin: 0 auto; }
                .card { background: white; padding: 25px 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 25px; }
                h1 { color: #1a365d; margin-top: 0; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }
                h2 { color: #2b6cb0; font-size: 1.3rem; margin-top: 0; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }
                th { background-color: #ebf8ff; color: #2c5282; font-weight: 600; }
                tr:hover { background-color: #f7fafc; }
                .badge-complete { background: #c6f6d5; color: #22543d; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
                .badge-pending { background: #feebc8; color: #744210; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85rem; }
                .form-group { display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap; }
                input[type="text"], input[type="password"], select { padding: 10px; border: 1px solid #cbd5e0; border-radius: 5px; flex: 1; min-width: 150px; }
                button { background: #3182ce; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
                button:hover { background: #2b6cb0; }
                .code-box { background: #1a202c; color: #63b3ed; padding: 15px; border-radius: 6px; font-family: monospace; font-size: 0.9rem; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card">
                    <h1>📌 PFO2 - Sistema de Gestión de Tareas (API REST)</h1>
                    <p>Bienvenido/a al panel web de supervisión de la base de datos de la <strong>PFO2 - Programación sobre Redes</strong>.</p>
                </div>

                <div class="card">
                    <h2>📋 Tareas Registradas en SQLite</h2>
                    {% if tareas %}
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Usuario</th>
                                <th>Título de la Tarea</th>
                                <th>Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for t in tareas %}
                            <tr>
                                <td>#{{ t.id }}</td>
                                <td><strong>{{ t.usuario }}</strong></td>
                                <td>{{ t.titulo }}</td>
                                <td>
                                    {% if t.completada %}
                                    <span class="badge-complete">✔ Completada</span>
                                    {% else %}
                                    <span class="badge-pending">⏳ Pendiente</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <p style="color: #718096;"><em>No hay tareas en la base de datos aún. Creá una desde el cliente CLI o con el formulario de abajo.</em></p>
                    {% endif %}
                </div>

                <div class="card">
                    <h2>👥 Usuarios Registrados</h2>
                    {% if usuarios %}
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Nombre de Usuario</th>
                                <th>Estado Contraseña</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for u in usuarios %}
                            <tr>
                                <td>#{{ u.id }}</td>
                                <td><strong>{{ u.usuario }}</strong></td>
                                <td><span style="color: #38a169;">Seguro (Password Hash Werkzeug)</span></td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <p style="color: #718096;"><em>No hay usuarios registrados aún.</em></p>
                    {% endif %}
                </div>

                <div class="card">
                    <h2>➕ Crear Tarea Rápida desde Web</h2>
                    <form action="/tareas" method="POST" class="form-group">
                        <select name="usuario" required>
                            <option value="">-- Seleccionar Usuario --</option>
                            {% for u in usuarios %}
                            <option value="{{ u.usuario }}">{{ u.usuario }}</option>
                            {% endfor %}
                        </select>
                        <input type="text" name="titulo" placeholder="Descripción de la tarea..." required>
                        <button type="submit">Guardar Tarea</button>
                    </form>
                </div>

                <div class="card">
                    <h2>🖥️ Cliente en Consola (CLI)</h2>
                    <p>Para interactuar mediante la terminal ejecutá el cliente Python incluido:</p>
                    <div class="code-box">python cliente.py</div>
                </div>
            </div>
        </body>
        </html>
        """
        return render_template_string(html_content, tareas=tareas_rows, usuarios=usuarios_rows)

    # Respuesta JSON para peticiones API / CLI
    if usuario:
        cursor.execute("""
            SELECT t.id, t.titulo, t.completada 
            FROM tareas t 
            JOIN usuarios u ON t.usuario_id = u.id 
            WHERE u.usuario = ?
        """, (usuario,))
    else:
        cursor.execute("SELECT id, titulo, completada FROM tareas")
        
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return jsonify({
        "mensaje": "Bienvenido al gestor de tareas.",
        "usuario_filtrado": usuario if usuario else "Todos",
        "total_tareas": len(tareas),
        "tareas": tareas
    }), 200

@app.route('/tareas', methods=['POST'])
def crear_tarea():
    """Crea una nueva tarea para un usuario registrado."""
    if request.is_json:
        data = request.get_json() or {}
        usuario = data.get('usuario')
        titulo = data.get('titulo')
    else:
        usuario = request.form.get('usuario')
        titulo = request.form.get('titulo')

    if not usuario or not titulo:
        return jsonify({"error": "Se requieren los campos 'usuario' y 'titulo'."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (usuario,))
    user_row = cursor.fetchone()
    
    if not user_row:
        conn.close()
        return jsonify({"error": f"El usuario '{usuario}' no existe."}), 404

    cursor.execute(
        "INSERT INTO tareas (usuario_id, titulo) VALUES (?, ?)",
        (user_row['id'], titulo)
    )
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()

    if not request.is_json and 'text/html' in request.headers.get('Accept', ''):
        return redirect('/tareas')

    return jsonify({
        "mensaje": "Tarea creada exitosamente.",
        "tarea": {"id": tarea_id, "usuario": usuario, "titulo": titulo, "completada": False}
    }), 201

@app.route('/tareas/<int:tarea_id>', methods=['PUT'])
def marcar_completada(tarea_id):
    """Marca una tarea como completada."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tareas SET completada = 1 WHERE id = ?", (tarea_id,))
    changes = conn.total_changes
    conn.commit()
    conn.close()

    if changes > 0:
        return jsonify({"mensaje": f"Tarea #{tarea_id} marcada como completada."}), 200
    else:
        return jsonify({"error": "Tarea no encontrada."}), 404

@app.route('/tareas/<int:tarea_id>', methods=['DELETE'])
def eliminar_tarea(tarea_id):
    """Elimina una tarea por su ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    changes = conn.total_changes
    conn.commit()
    conn.close()

    if changes > 0:
        return jsonify({"mensaje": f"Tarea #{tarea_id} eliminada exitosamente."}), 200
    else:
        return jsonify({"error": "Tarea no encontrada."}), 404

if __name__ == '__main__':
    init_db()
    print("==========================================")
    print(" Servidor API REST PFO2 escuchando en:")
    print(" http://localhost:5000")
    print("==========================================")
    app.run(host='localhost', port=5000, debug=True)
