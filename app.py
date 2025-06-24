from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, render_template
from supabase import create_client, Client
import psycopg2
import json

import os


app = Flask(__name__)



DATABASE_URL = "postgresql://postgres:komic2025!db@db.jeboojuntugrognjvlzc.supabase.co:5432/postgres"
#DATABASE_URL = os.environ.get("postgresql://postgres:komic2025!db@db.jeboojuntugrognjvlzc.supabase.co:5432/postgres")


SUPABASE_URL = "https://jeboojuntugrognjvlzc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImplYm9vanVudHVncm9nbmp2bHpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2MTk0MjMsImV4cCI6MjA2NjE5NTQyM30.iLQBgkRnXWZYljoSvkvaFLZC8RIaIqZxiziirniLeJQ" 
BUCKET_NAME = "archivos"  

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn




@app.route('/subir', methods=['POST'])
def subir_archivo():
    if 'archivo' not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400

    archivo = request.files['archivo']
    nombre_archivo = archivo.filename

    contenido = archivo.read()

    try:
        resultado = supabase.storage.from_(BUCKET_NAME).upload(nombre_archivo, contenido, {"content-type": archivo.mimetype})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{nombre_archivo}"

    return jsonify({"mensaje": "Archivo subido correctamente", "url": url})



@app.route('/form-subir')
def form_subir():
    return render_template('formulario_subida.html')





@app.route('/')
def home():
    return jsonify({"mensaje": "¡Hola desde Render con Flask!"})

@app.route('/create_table')
def create_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            username VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Tabla usuarios creada o ya existente"})






from werkzeug.security import generate_password_hash, check_password_hash

@app.route('/form')
def form():
    return render_template('formulario.html')



@app.route('/signup', methods=['POST'])
def signup():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({"error": "Faltan username o password"}), 400

    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (username, hashed_password))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"mensaje": "Usuario registrado correctamente"})
    except psycopg2.errors.UniqueViolation:
        return jsonify({"error": "El username ya existe"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500





@app.route('/sesion')
def login_form():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
    else:
        username = request.form.get('username')
        password = request.form.get('password')

    if not username or not password:
        return jsonify({"error": "Faltan username o password"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM usuarios WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[0], password):
            return jsonify({"mensaje": "Login exitoso"})
        else:
            return jsonify({"error": "Usuario o contraseña incorrectos"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500







@app.route('/drop_table')
def drop_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios;")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Tabla usuarios eliminada"})



@app.route('/listar', methods=['GET'])
def listar_usuarios():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password FROM usuarios;")
    usuarios = cur.fetchall()
    cur.close()
    conn.close()

    resultado = []
    for usuario in usuarios:
        resultado.append({
            "id": usuario[0],
            "username": usuario[1],
            "password": usuario[2]
        })

    return jsonify(resultado)






@app.route('/ver_imagen')
def ver_imagen():
    url = "https://jeboojuntugrognjvlzc.supabase.co/storage/v1/object/public/archivos/gato.jpg"
    return render_template('mostrar.html', url=url)


@app.route('/ver_pdf')
def ver_pdf():
    url = "https://jeboojuntugrognjvlzc.supabase.co/storage/v1/object/public/archivos/gato.pdf"
    return render_template('mostrarpdf.html', url=url)


@app.route('/mapa')
def mapa():
    return render_template('mapa.html')




@app.route('/hospitales_geojson', methods=['GET'])
def hospitales_geojson():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, ST_AsGeoJSON(geom) AS geometry, nombre, descrip
            FROM hospital;
        """)
        rows = cur.fetchall()
        print(f"Datos recibidos: {rows}")  # 👈 Esto lo verás en los logs
        cur.close()
        conn.close()

        features = []
        for row in rows:
            geometry = row[1]
            if geometry:
                features.append({
                    "type": "Feature",
                    "geometry": json.loads(geometry),
                    "properties": {
                        "id": row[0],
                        "nombre": row[2],
                        "descrip": row[3]
                    }
                })

        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        return jsonify(geojson)
    except Exception as e:
        print(f"Error en hospitales_geojson: {str(e)}")  # 👈 También en logs de Render
        return jsonify({"error": str(e)}), 500



@app.route('/tablas')
def listar_tablas():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tablas = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify([t[0] for t in tablas])
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route('/ciudad')
def ver_ciudad():
    return render_template('ciudad.html')





if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


