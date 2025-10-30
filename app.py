from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from supabase import create_client, Client, PostgrestAPIError, AuthApiError
from dotenv import load_dotenv
import os

# Configuración básica
load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

TEMPLATE_LOGIN = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Login</title>
<style>
body { font-family: Arial; background: #f6f7fb; display: flex; justify-content: center; align-items: center; height: 100vh; }
form { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px #ccc; }
input { display: block; margin: 10px 0; padding: 8px; width: 250px; }
button { padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
</style></head>
<body>
<form method="POST" action="/login">
  <h2> Sistema de registro de tareas </h2>
  <h4> Iniciar sesión</h4>
  <input type="email" name="email" placeholder="Correo electrónico" required>
  <input type="password" name="password" placeholder="Contraseña" required>
  <button type="submit">Entrar</button>
  <p>¿No tienes cuenta? <a href="/register">Regístrate</a></p>
  {% if error %}<p style="color:red;">{{error}}</p>{% endif %}
  {% with messages = get_flashed_messages(with_categories=true) %}{% for category, message in messages %}<p style="color:{{'green' if category == 'success' else 'red'}};">{{ message }}</p>{% endfor %}{% endwith %}
</form></body></html>
"""

TEMPLATE_REGISTER = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Registro</title>
<style>
body { font-family: Arial; background: #f6f7fb; display: flex; justify-content: center; align-items: center; height: 100vh; }
form { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px #ccc; }
input { display: block; margin: 10px 0; padding: 8px; width: 250px; }
button { padding: 8px 15px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; }
</style></head>
<body>
<form method="POST" action="/register">
  <h2> Crear cuenta</h2>
  <input type="email" name="email" placeholder="Correo electrónico" required>
  <input type="password" name="password" placeholder="Contraseña" required>
  <button type="submit">Registrarme</button>
  <p><a href="/login">Volver al login</a></p>
  {% if error %}<p style="color:red;">{{error}}</p>{% endif %}
</form></body></html>
"""

TEMPLATE_TASKS = """
<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8"><title>Tareas</title>
<style>
body { font-family: Arial; background: #f6f7fb; margin: 40px; }
h1 { color: #333; }
form { margin-bottom: 20px; }
input[type=text] { padding: 8px; width: 300px; }
button { padding: 8px 15px; background: #007bff; color: white; border: none; cursor: pointer; border-radius: 4px; }
button:hover { background: #0056b3; }
table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; }
th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }
tr:hover { background: #f1f1f1; }
</style></head>
<body>
  {% with messages = get_flashed_messages(with_categories=true) %}{% for category, message in messages %}<p style="color:{{'green' if category == 'success' else 'red'}};">{{ message }}</p>{% endfor %}{% endwith %}
  <h1> Tareas de {{email}}</h1>
  <form method="POST" action="/add">
    <input type="text" name="title" placeholder="Nueva tarea..." required>
    <button type="submit">Agregar</button>
  </form>
  <table>
    <tr><th>ID</th><th>Título</th><th>Estado</th><th>Acción</th></tr>
    {% for t in tasks %}
    <tr>
        <td>{{t['id']}}</td>
        <td>{{t['title']}}</td>
        <td>{{"✔️" if t['done'] else "❌"}}</td>
        <td>
            {% if not t['done'] %}
                <a href="/done/{{t['id']}}">Marcar completada</a>
            {% else %}
                <a href="/delete/{{t['id']}}">Eliminar</a>
            {% endif %}
        </td>
    </tr>
    {% endfor %}
  </table>
  <p><a href="/logout">Cerrar sesión</a></p>
</body></html>
"""

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    user_email = session["user_email"]
    res = supabase.table("task").select("*").eq("user_id", user_id).execute()
    return render_template_string(TEMPLATE_TASKS, tasks=res.data, email=user_email)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        try:
            result = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if result.user:
                session["user_id"] = result.user.id
                session["user_email"] = result.user.email
                print(f"DEBUG: User {email} logged in successfully. User ID: {result.user.id}") 
                return redirect("/")
            return render_template_string(TEMPLATE_LOGIN, error="Credenciales incorrectas.")
        except AuthApiError as e:
            return render_template_string(TEMPLATE_LOGIN, error=e.message)
        except Exception as e:
            return render_template_string(TEMPLATE_LOGIN, error=f"Error inesperado: {e}")
    return render_template_string(TEMPLATE_LOGIN)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            result = supabase.auth.sign_up({"email": email, "password": password})
            if result.user:
                flash("¡Registro exitoso! Ahora puedes iniciar sesión.", "success")
                return redirect(url_for("login"))
            else:
                flash("No se pudo completar el registro. Inténtalo de nuevo.", "error")
        except (AuthApiError, Exception) as e:
            return render_template_string(TEMPLATE_REGISTER, error=str(e))

    return render_template_string(TEMPLATE_REGISTER)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/login")
    title = request.form["title"]
    user_id = session["user_id"]
    try:
        supabase.table("task").insert({"title": title, "done": False, "user_id": user_id}).execute()
        flash("Tarea agregada exitosamente.", "success")
    except (PostgrestAPIError, Exception) as e:
        print(f"ERROR AL INSERTAR: {getattr(e, 'message', e)}")
        flash(f"Error al agregar la tarea: {getattr(e, 'message', e)}", "error")
    return redirect("/")

@app.route("/done/<int:task_id>")
def done(task_id):
    if "user_id" not in session:
        return redirect("/login")
    user_id = session["user_id"]
    try:
        supabase.table("task").update({"done": True}).eq("id", task_id).eq("user_id", user_id).execute()
        flash("Tarea marcada como completada.", "success")
    except (PostgrestAPIError, Exception) as e:
        flash(f"No se pudo actualizar la tarea: {getattr(e, 'message', e)}", "error")
    return redirect("/")

@app.route("/delete/<int:task_id>")
def delete(task_id):
    if "user_id" not in session:
        return redirect("/login")
    try:
        user_id = session["user_id"]
        supabase.table("task").delete().eq("id", task_id).eq("user_id", user_id).execute()
        flash("Tarea eliminada exitosamente.", "success")
    except (PostgrestAPIError, Exception) as e:
        flash(f"No se pudo eliminar la tarea: {getattr(e, 'message', e)}", "error")
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)