import sqlite3
import hashlib
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

DB_NAME = "usuarios.db"
PORT = 5800
USUARIOS = [
    ("Reynaldo Millanguir", "123456"),
    ("admin", "admin123")
]

def inicializar_bd():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)
    for username, password in USUARIOS:
        hash_obj = hashlib.sha256(password.encode())
        password_hash = hash_obj.hexdigest()
        cursor.execute(
            "INSERT OR IGNORE INTO usuarios (username, password_hash) VALUES (?, ?)",
            (username, password_hash)
        )
    conn.commit()
    conn.close()

def validar_usuario(username, password):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    hash_obj = hashlib.sha256(password.encode())
    password_hash = hash_obj.hexdigest()
    cursor.execute(
        "SELECT * FROM usuarios WHERE username = ? AND password_hash = ?",
        (username, password_hash)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None

def listar_usuarios():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM usuarios")
    rows = cursor.fetchall()
    conn.close()
    return rows

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        if path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"><title>Gestion de Usuarios</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                form { margin: 20px 0; padding: 20px; border: 1px solid #ccc; border-radius: 8px; max-width: 400px; }
                input { display: block; margin: 10px 0; padding: 8px; width: 100%; }
                button { padding: 10px 20px; background: #4CAF50; color: white; border: none; cursor: pointer; }
                table { border-collapse: collapse; width: 100%; max-width: 600px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background: #f2f2f2; }
                .error { color: red; }
                .success { color: green; }
            </style>
            </head>
            <body>
                <h1>Gestion de Usuarios</h1>
                <h2>Login</h2>
                <form method="GET" action="/login">
                    <input type="text" name="username" placeholder="Usuario" required>
                    <input type="password" name="password" placeholder="Contrasena" required>
                    <button type="submit">Ingresar</button>
                </form>
                <h2>Usuarios Registrados</h2>
                <table>
                    <tr><th>ID</th><th>Username</th><th>Password Hash (SHA-256)</th></tr>
            """
            for uid, uname, phash in listar_usuarios():
                html += f"<tr><td>{uid}</td><td>{uname}</td><td>{phash}</td></tr>"
            html += """
                </table>
                <p><small>Hash SHA-256 de las contrasenas almacenadas en SQLite</small></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode("utf-8"))

        elif path == "/login":
            username = params.get("username", [""])[0]
            password = params.get("password", [""])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            if validar_usuario(username, password):
                html = f"""
                <!DOCTYPE html>
                <html><head><meta charset="utf-8"><title>Login Exitoso</title>
                <style>body {{ font-family: Arial; margin: 40px; }} .success {{ color: green; }}</style>
                </head><body>
                <h1 class="success">Login Exitoso</h1>
                <p>Bienvenido, <strong>{username}</strong>!</p>
                <p>Usuario validado correctamente.</p>
                <a href="/">Volver</a>
                </body></html>
                """
            else:
                html = f"""
                <!DOCTYPE html>
                <html><head><meta charset="utf-8"><title>Login Fallido</title>
                <style>body {{ font-family: Arial; margin: 40px; }} .error {{ color: red; }}</style>
                </head><body>
                <h1 class="error">Credenciales Invalidas</h1>
                <p>Usuario o contrasena incorrectos.</p>
                <a href="/">Intentar de nuevo</a>
                </body></html>
                """
            self.wfile.write(html.encode("utf-8"))

        elif path == "/api/usuarios":
            self.send_response(200)
            self.send_header("Content-type", "application/json; charset=utf-8")
            self.end_headers()
            usuarios = []
            for uid, uname, phash in listar_usuarios():
                usuarios.append({"id": uid, "username": uname, "password_hash": phash})
            self.wfile.write(json.dumps(usuarios, indent=2).encode("utf-8"))

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>404 - Pagina no encontrada</h1>")

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {args[0]} {args[1]} {args[2]}")

if __name__ == "__main__":
    inicializar_bd()
    print(f"=== Sistema de Gestion de Usuarios ===")
    print(f"Base de datos: {DB_NAME}")
    print(f"Usuarios registrados:")
    for uid, uname, phash in listar_usuarios():
        print(f"  - {uname}: {phash[:20]}...")
    print(f"\nServidor web iniciado en http://localhost:{PORT}")
    print(f"Abra http://localhost:{PORT} en su navegador")
    print(f"Presione Ctrl+C para detener el servidor")
    server = HTTPServer(("localhost", PORT), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        server.server_close()
