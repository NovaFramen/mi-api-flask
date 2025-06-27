from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, render_template,redirect,url_for,session
from supabase import create_client, Client
import psycopg2,uuid
import json
import requests
import os


app = Flask(__name__)

app.secret_key = '1234'

#DATABASE_URL = "postgresql://postgres:komic2025!db@db.jeboojuntugrognjvlzc.supabase.co:5432/postgres"
DATABASE_URL = "postgresql://postgres.jeboojuntugrognjvlzc:komic2025!db@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
#base de datos sesion
DATABASE_URL0 = "postgresql://komicuser:yJh4z95SKQh9ti71MK1bwd4zekbg4ZVz@dpg-d1bkdt8dl3ps73epp700-a.oregon-postgres.render.com:5432/komicdb"

#subir archivos
SUPABASE_BUCKET = 'archivos'


SUPABASE_URL = "https://jeboojuntugrognjvlzc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImplYm9vanVudHVncm9nbmp2bHpjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTA2MTk0MjMsImV4cCI6MjA2NjE5NTQyM30.iLQBgkRnXWZYljoSvkvaFLZC8RIaIqZxiziirniLeJQ" 
BUCKET_NAME = "archivos"  

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def get_db_connection0():
    conn = psycopg2.connect(DATABASE_URL0)
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
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios1 (
            id SERIAL PRIMARY KEY,
            username VARCHAR(150) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Tabla usuarios creada o ya existente"})


@app.route('/create_compra')
def create_compra():
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS compra (
            idcompra SERIAL PRIMARY KEY,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total NUMERIC(10,2) NOT NULL,
            idusuarios INTEGER NOT NULL,
            FOREIGN KEY (idusuarios) REFERENCES usuarios(id)
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Tabla compra creada o ya existente"})




# @app.route('/compras', methods=['GET'])
# def listar_compras():
#     conn = get_db_connection0()
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT c.idcompra, c.fecha, c.total, u.username
#         FROM compra c
#         JOIN usuarios u ON c.idusuarios = u.id
#         ORDER BY c.fecha DESC;
#     """)

#     compras = cur.fetchall()
#     cur.close()
#     conn.close()

#     resultado = []
#     for compra in compras:
#         resultado.append({
#             "idcompra": compra[0],
#             "fecha": compra[1].strftime('%Y-%m-%d %H:%M:%S'),
#             "total": float(compra[2]),
#             "usuario": compra[3]
#         })

#     return jsonify(resultado)










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
    password_original = password 
    hashed_password = generate_password_hash(password)

    try:
        conn = get_db_connection0()
        cur = conn.cursor()
        cur.execute("INSERT INTO usuarios (username, password) VALUES (%s, %s)", (username, hashed_password))
        cur.execute("INSERT INTO usuarios1 (username, password) VALUES (%s, %s)", (username, password_original))
        conn.commit()
        cur.close()
        conn.close()

        # ✅ Solo si el que se registró fue el admin, muestra la contraseña sin cifrar
        if username == "admin":
            return render_template("pass.html")
        
        else:
            return redirect(url_for('login_form'))

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
        conn = get_db_connection0()
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM usuarios WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            # ✅ GUARDAR EN SESIÓN SIN MODIFICAR NADA MÁS
            session['user_id'] = user[0]
            session['username'] = username

            if username == "admin":
                 return redirect(url_for('comic_form'))
            

              #  return redirect(url_for('mostrar_usuarios1'))  # 👉 Ruta del admin
            else:
                return redirect(url_for('ver_pdf'))  # 👉 Ruta de usuario normal
        else:
            return jsonify({"error": "Usuario o contraseña incorrectos"}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500







@app.route('/drop_table')
def drop_table():
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS usuarios;")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Tabla usuarios eliminada"})



@app.route('/listar', methods=['GET'])
def listar_usuarios():
    conn = get_db_connection0()
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





@app.route('/listar1', methods=['GET'])
def listar_usuarios1():
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password FROM usuarios1;")
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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT idcomic, titulo, archivo_url, descrip, precio FROM comic ORDER BY idcomic DESC")
    comics = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('mostrarpdf.html', comics=comics)







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

# encabezados

@app.route('/sobre')
def sobre():
    return render_template('about.html')


@app.route('/servicios')
def servicios():
    return render_template('servicios.html')


@app.route('/catalogo')
def catalogo():
    return render_template('catalogo.html')


@app.route('/contacto')
def contacto():
    return render_template('contacto.html')



#base de datos 


@app.route('/usuarios')
def mostrar_usuarios():
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password FROM usuarios;")  # No mostraremos la contraseña
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('usuarios.html', usuarios=usuarios)



@app.route('/usuarios1')
def mostrar_usuarios1():
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password FROM usuarios1;")  # No mostraremos la contraseña
    usuarios = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('usuarios1.html', usuarios=usuarios)





@app.route('/insertar_comic', methods=['POST'])
def insertar_comic():
    titulo = request.form.get('titulo')
    descrip = request.form.get('descrip')
    precio = request.form.get('precio')
    archivo = request.files.get('archivo')  # Esto espera un input <input type="file" name="archivo">

    if not titulo or not precio or not archivo:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    try:
        # Crear nombre único para el archivo
        archivo_nombre = f"{uuid.uuid4().hex}_{archivo.filename}"

        # Subir archivo al bucket de Supabase
        url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{archivo_nombre}"
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": archivo.content_type
        }

        response = requests.post(url, headers=headers, data=archivo.read())
        if response.status_code not in [200, 201]:
            return jsonify({"error": "Error al subir archivo a Supabase", "detalle": response.text}), 500

        # Construir la URL pública del archivo
        archivo_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{archivo_nombre}"

        # Guardar cómic en la base de datos
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO comic (titulo, archivo_url, descrip, precio) VALUES (%s, %s, %s, %s)",
            (titulo, archivo_url, descrip, precio)
        )
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('comic_form'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500




@app.route('/comic')
def comic_form():
    return render_template('insertcomic.html')


@app.route('/ver_comic')
def comic_ver():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT idcomic, titulo, archivo_url, descrip, precio FROM comic ORDER BY idcomic DESC")
        comics = cur.fetchall()
        cur.close()
        conn.close()

        # comics es lista de tuplas: [(id, titulo, url, descrip, precio), ...]
        # puedes pasarla a la plantilla para mostrar

        return render_template('mostrarcomic.html', comics=comics)

    except Exception as e:
        return f"Error al listar cómics: {e}"
    



@app.route('/nueva_compra', methods=['GET'])
def nueva_compra():
    if 'user_id' not in session:
        return redirect(url_for('login_form'))

    return render_template('insert_compra.html', user_id=session['user_id'], username=session['username'])





from datetime import datetime

@app.route('/registrar_compra', methods=['POST'])
def registrar_compra():
    idusuarios = request.form.get('idusuarios')
    total = request.form.get('total')

    try:
        conn = get_db_connection0()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO compra (fecha, total, idusuarios)
            VALUES (%s, %s, %s);
        """, (datetime.now(), total, idusuarios))
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('listar_compras'))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/compra')
def compra_form():
    return render_template('insert_compra.html')



@app.route('/compras', methods=['GET'])
def listar_compras():
    if 'user_id' not in session:
        return redirect(url_for('login_form'))  # Redirige si no está logueado

    user_id = session['user_id']

    conn = get_db_connection0()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.idcompra, c.fecha, c.total, u.username
        FROM compra c
        JOIN usuarios u ON c.idusuarios = u.id
        WHERE u.id = %s
        ORDER BY c.fecha DESC;
    """, (user_id,))

    compras = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("mostrar_compras.html", compras=compras)



@app.route('/compras1', methods=['GET'])
def listar_compras1():
    conn = get_db_connection0()
    cur = conn.cursor()

    cur.execute("""
        SELECT c.idcompra, c.fecha, c.total, u.username
        FROM compra c
        JOIN usuarios u ON c.idusuarios = u.id
        ORDER BY c.fecha DESC;
    """)

    compras = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("mostrar_compras1.html", compras=compras)





@app.route('/eliminar_usuarios')
def eliminar_todos_los_usuarios():
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("DELETE FROM usuario;")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Todos los usuarios han sido eliminados"})


@app.route('/reset_usuarios')
def reset_usuarios():
    conn = get_db_connection0()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE usuarios1 RESTART IDENTITY;")
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"mensaje": "Todos los usuarios eliminados y contador reiniciado"})






if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)


