from datetime import datetime
#import sqlite3
#import oauth
from oauthlib.oauth2 import WebApplicationClient
import psycopg2
import unicodedata
from flask_login import LoginManager, login_user, UserMixin,logout_user ,current_user
from flask import Flask, render_template, request, redirect, session, flash, jsonify, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import os
import random
from dotenv import load_dotenv
from datetime import timedelta
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(hours=1)
#DB_PATH = 'base_resto.db'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

oauth = OAuth(app)
oauth.register(
name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    #access_token_url='https://accounts.google.com/o/oauth2/token',
    #authorize_url='https://accounts.google.com/o/oauth2/auth',
    #api_base_url='https://www.googleapis.com/oauth2/v1/',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    #userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# 🔐 Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_user"

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connction():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', 5432)

    )

def init_db():
    #conn = sqlite3.connect(DB_PATH)
    conn = get_db_connction()
    cur = conn.cursor()
    #cur.execute('DROP TABLE IF EXISTS users')
    #cur.execute("ALTER TABLE users RENAME COLUMN nom TO username")
    cur.execute('''
                    CREATE TABLE IF NOT EXISTS super_admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL
                    )
                ''')
    print("Table super_admins créée")

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

    print("Table admins créée")
    cur.execute('''
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nom TEXT NOT NULL,
                            email TEXT UNIQUE NOT NULL,
                            password TEXT ,
                            oauth_provider TEXT ,
                            oauth_id TEXT,
                            google_access_token TEXT,
                            google_refresh_token TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    ''')
    print("Table user créée")

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS reservations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prenom TEXT NOT NULL,
                        nom TEXT NOT NULL,
                        n_places TEXT NOT NULL,
                        heur TIMESTAMP NOT NULL,
                        created_at TIMESTAMP NOT NULL
                    )
    ''')
    print("Table réservations créée")

    cur.execute('''
                    CREATE TABLE IF NOT EXISTS commandes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prenom TEXT NOT NULL,
                        nom TEXT NOT NULL,                        
                        address TEXT NOT NULL,
                        tel VARCHAR(9) NOT NULL,
                        total REAL,
                        created_at TIMESTAMP NOT NULL
                    )
        ''')
    print("Table commandes créée")
    #cur.execute("ALTER TABLE menu_items ADD image BLOB")
    #cur.execute("ALTER TABLE menu_items DROP COLUMN total")
    cur.execute('''
                       CREATE TABLE IF NOT EXISTS menu_items (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           nom TEXT NOT NULL,
                           description TEXT,
                           prix REAL NOT NULL,
                           image BLOB,
                           categorie TEXT NOT NULL
                       )
           ''')

    print("Table menu_items créée")
    cur.execute('''
                           CREATE TABLE IF NOT EXISTS commande_items (
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               commande_id INTEGER NOT NULL,
                               menu_id INTEGER NOT NULL,
                               quantite INTEGER NOT NULL,
                               prix_unitaire REAL NOT NULL,
                               FOREIGN KEY (commande_id) REFERENCES commandes(id),
                               FOREIGN KEY (menu_id) REFERENCES menu_items(id)
                           )
               ''')
    print("Table commande_items créée")
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM admins")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO admins (username, password) VALUES (%s, %s)", (
            "admin",
            generate_password_hash("admin123")
        ))
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM super_admins")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO super_admins (username, password) VALUES (%s, %s)", (
            "superadmin",
            generate_password_hash("superadmin123")
        ))
    conn.commit()
    cur.close()
    conn.close()

def normalize_txt(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')

@app.route('/')
def index():
    return render_template('home.html')

#login super admin
@app.route('/super_admin', methods=['GET', 'POST'])
def login_super_admin():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        conn = get_db_connction()
        cur = conn.cursor()
        cur.execute('SELECT password FROM super_admins WHERE username = %s', (user,))
        data = cur.fetchone()
        conn.close()

        if data and check_password_hash(data[0], pw):
            session['super_admin'] = user
            return redirect('/super_admin/dashbord')
        else:
            return "Identifiants incorrects", 403
    return render_template('login_supadmin.html')

#dashbord super admin
@app.route('/super_admin/dashbord')
def super_admin():
    if 'super_admin' not in session:
        return redirect('/super_admin')
    #conn = sqlite3.connect(DB_PATH)
    conn = get_db_connction()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admins ORDER BY created_at DESC")
    admins = cur.fetchall()
    admins_dicts = [{
        'id': r[0],
        'username': r[1],
        'password': r[2],
        'created_at': r[3],

    } for r in admins]
    conn.close()
    return render_template('dashboard_supadmin.html', admins=admins, admins_json=admins_dicts)

@app.route('/super_admin/search', methods=['GET'])
def search_admin():
    a = request.args.get('a', '').strip()
    conn=get_db_connction()
    #conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if a:
        like_a = f"%{a}%"

        cur.execute("""
          SELECT id, username
          FROM admins
          WHERE id          LIKE %s
             OR username    LIKE %s

        """, (like_a, like_a))

    else:
        cur.execute("""
                  SELECT id, username
                  FROM admins
                  ORDER BY created_at DESC
                """)
    admins = cur.fetchall()
    conn.close()
    if request.args.get('ajax'):
        # Prépare la liste de dicts
        results = [{
            'id': r[0],
            'username': r[1],
        } for r in admins]
        return jsonify(results)

    return render_template('dashboard_superadmin.html', admins=admins, a=a)

@app.route('/super_admin/logout')
def logout_supadmin():
    session.pop('super_admin', None)
    return redirect('/super_admin')

#login admin
@app.route('/admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        conn=get_db_connction()
        #conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT password FROM admins WHERE username = %s', (user,))
        data = cur.fetchone()
        conn.close()

        if data and check_password_hash(data[0], pw):
            session['admin'] = user
            return redirect('/admin/dashbord')
        else:
            return "Identifiants incorrects", 403
    return render_template('login_admin.html')


def get_all_commandes():
    conn = get_db_connction()
    #conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM commandes ORDER BY created_at DESC")
    commandes = cur.fetchall()
    cur.close()
    conn.close()
    return commandes
def get_all_menu_items():
    conn=get_db_connction()
    #conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM menu_items ")
    menus = cur.fetchall()
    cur.close()
    conn.close()
    return menus

#dashbord admin
@app.route('/admin/dashbord')
def admin():
    if 'admin' not in session:
        return redirect('/admin')
    section = request.args.get("section", "commandes")

    commandes = []
    commandes_dicts = []
    menus = []
    menus_dicts = []
    data = None

    conn = get_db_connction()
    #conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    if section == "commandes":
        cur.execute("SELECT * FROM commandes")
        commandes = cur.fetchall()
        commandes_dicts = [{
            'id': r[0],
            'prenom': r[1],
            'nom': r[2],
            'address': r[3],
            'tel': r[4],
            'total': r[5],
            'created_at': r[6],
        } for r in commandes]
        conn.close()
        data = get_all_commandes()

    if section == "menu":
        # Charger les plats/menu
        cur.execute("SELECT * FROM menu_items")
        menus = cur.fetchall()
        menus_dicts = [{
            'id': r[0],
            'nom': r[1],
            'description': r[2],
            'prix': r[3],
            'image': r[4],
            'categorie': r[5],
        } for r in menus]
        conn.close()
        data = get_all_menu_items()

    return render_template('dashboard_admin.html', commandes=commandes, commandes_json=commandes_dicts,
                           menus=menus, menus_json=menus_dicts, section=section, data=data)

@app.route('/admin/search_commandes', methods=['GET'])
def search_commandes():
    n = request.args.get('n', '').strip()
    conn = get_db_connction()
    #conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if n:
        like_q = f"%{n}%"

        cur.execute("""
                  SELECT id, prenom, nom, address,tel , total, created_at
                  FROM commandes
                  WHERE id LIKE %s
                     OR prenom    LIKE %s
                     OR nom    LIKE %s
                     OR address LIKE %s
                     OR tel LIKE %s
                     OR total LIKE %s
                     OR created_at LIKE %s

                """, (like_q, like_q, like_q, like_q, like_q, like_q, like_q))
    else:
        cur.execute("""SELECT id, prenom, nom, address,tel , total, created_at
                  FROM commandes ORDER BY created_at DESC """)
    commandes = cur.fetchall()
    conn.close()

    if request.args.get('ajax'):
        # Prépare la liste de dicts
        results = [{
            'id': r[0],
            'prenom': r[1],
            'nom': r[2],
            'address': r[3],
            'tel': r[4],
            'total': r[5],
            'created_at': r[6]
        } for r in commandes]
        return jsonify(results)

    return render_template('dashboard_admin.html', commandes=commandes, menus=[], n=n)

@app.route('/admin/search_menus', methods=['GET'])
def search_menus():
    f = request.args.get('f', '').strip()
    conn = get_db_connction()
    cur = conn.cursor()
    if f:
        like_q = f"%{f}%"

        cur.execute("""
                  SELECT id, nom, description, prix, image , categorie
                  FROM menu_items
                  WHERE id    LIKE %s
                     OR nom    LIKE %s
                     OR description LIKE %s
                     OR prix LIKE %s
                     OR image LIKE %s
                     OR categorie LIKE %s

                """, (like_q, like_q, like_q, like_q, like_q, like_q))
    else:
        cur.execute("""SELECT id, nom, description, prix, image , categorie
                  FROM menu_items ORDER BY nom ASC """)
    menus = cur.fetchall()
    conn.close()

    if request.args.get('ajax'):
        # Prépare la liste de dicts
        results = [{
            'id': r[0],
            'nom': r[1],
            'description': r[2],
            'prix': r[3],
            'image': r[4],
            'categorie': r[5],

        } for r in menus]
        return jsonify(results)

    return render_template('dashboard_admin.html', menus=menus, f=f)

@app.route('/edit_menu/<int:id>', methods=['GET', 'POST'])
def edit_menu(id):
    if 'admin' not in session:
        return redirect('/admin')

    conn=get_db_connction()
    #conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Récupération des données existantes
    cur.execute('SELECT * FROM menu_items WHERE id=%s', (id,))
    menu_item = cur.fetchone()

    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        description = request.form.get('description', '').strip()
        prix = request.form.get('prix', '').strip()
        categorie = request.form.get('categorie', '').strip()

        # Gestion du champ image
        image_data = menu_item[4]  # index du champ image dans le tuple (si tu veux garder l’ancienne)
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file and image_file.filename != '':
                image_data = image_file.read()

        # Mise à jour dans la base
        cur.execute('''
            UPDATE menu_items
            SET nom = %s, description = %s, prix = %s, image = %s, categorie = %s
            WHERE id = %s
        ''', (nom, description, prix, image_data, categorie, id))

        conn.commit()
        conn.close()
        return redirect('/admin/dashbord')

    conn.close()
    return render_template('edit_menu.html', men=menu_item)

@app.route('/admin/logout')
def logout_admin():
    session.pop('admin', None)
    return redirect('/admin')

#login user
@app.route('/user')
def login_user_route():
    if request.method == 'POST':
        email = request.form['email']
        pw = request.form['password']
        conn=get_db_connction()
        #conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute('SELECT id,username, password FROM users WHERE email = %s', (email,))
        data = cur.fetchone()
        conn.close()

        if data and check_password_hash(data[2], pw):
            session['users'] = {
                'id': data["id"],
                'username': data["username"],
                'email': email
            }
            user = User(id=data["id"], username=data["username"], email="email")
            login_user(user)
            return redirect('/home')
        else:
            return "Identifiants incorrects", 403
    return render_template('login_user.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get("confirm_password")
        accept_terms = request.form.get("acceptTerms")
        print("Form POST data:", request.form.to_dict())

        #Validation simple
        if not all([username, email, password, confirm_password, accept_terms]):
            print("Validation échouée: champ(s) manquant(s)")
            flash("Tous les champs sont obligatoires.")
            return redirect(url_for("register"))

        if password != confirm_password:
            print("Validation échouée: mots de passe différents")
            flash("Les mots de passe ne correspondent pas.")
            return redirect(url_for("register"))

        hashed_pw = generate_password_hash(password)

        try:
            with get_db_connction() as conn:
                cur = conn.cursor()
                 #Vérifier si l'email existe déjà
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if cur.fetchone():
                    flash("Cet email est déjà enregistré.")
                    return redirect(url_for("login_user"))

                # Insérer en base
                cur.execute("""
                    INSERT INTO users (username, email, password, oauth_provider, oauth_id, google_access_token, google_refresh_token)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (username, email, hashed_pw,'','','','' ))

                conn.commit()
                flash("Compte créé avec succès, connectez-vous.")
                return render_template("login_user.html"), 200

        except Exception as e:
            print("Erreur SQL:", e)
            flash("Erreur interne.")
            return redirect(url_for("login_user"))
    return render_template("login_user.html")

@login_manager.user_loader
def load_user(user_id):
    try:
        conn=get_db_connction()
        #conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, username, email FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        conn.close()

        if row:
            return User(id=row["id"], username=row["username"], email=row["email"])
        return None
    except Exception:
        return None

@app.route("/google")
def google_login():
    redirect_uri = url_for("google_authorize", _external=True)
    print("Redirect URI envoyée à Google :", redirect_uri)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/google/signup")
def google_signup():
    redirect_uri = url_for("google_authorized", _external=True)
    print("Redirect URI envoyée à Google :", redirect_uri)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/login/google/authorized")
def google_authorize():
    # 1. Récupération du token
    token = oauth.google.authorize_access_token()
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")

    # 2. Infos profil Google (URL complète = plus sûr)
    resp = oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo")
    info = resp.json()
    email = info.get("email")
    oauth_id = info.get("sub") or info.get("id")
    username = info.get("name") or (email.split("@")[0] if email else None)

    if not email:
        flash("Impossible de récupérer l'email depuis Google.")
        return redirect(url_for("login_user"))

    # 3. Connexion BDD
    conn = get_db_connction()
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cur.fetchone()

    if not existing_user:
        return redirect(url_for('login_user_route', tab='register', username=username, email=email))
        #return redirect("/" + "?tab=register&from_google=1")
    else:
        cur.execute("""
                    UPDATE users
                    SET google_access_token = %s, google_refresh_token = %s
                    WHERE id = %s
                """, (access_token, refresh_token, existing_user["id"]))
        conn.commit()
        row = existing_user
    conn.close()

    # 4. Session Flask-Login
    user = User(id=row["id"], username=row["username"], email=row["email"])
    login_user(user)
    flash("Connexion Google réussie.")
    return redirect("/")

@app.route("/signup/google/authorized")
def google_authorized():
    token = oauth.google.authorize_access_token()
    access_token = token.get("access_token")
    refresh_token = token.get("refresh_token")
    resp = oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo")
    info = resp.json()
    email = info.get("email")
    oauth_id = info.get("sub") or info.get("id")
    username = info.get("name") or (email.split("@")[0] if email else None)

    if not email:
        flash("Impossible de récupérer l'email depuis Google.")
        return redirect(url_for("login_user"))
    conn = get_db_connction()
    #conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cur.fetchone()

    if not existing_user:
        cur.execute("""
            INSERT INTO users (username, email, oauth_provider, oauth_id, google_access_token, google_refresh_token)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (username, email, "google", oauth_id, access_token, refresh_token))
        conn.commit()
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cur.fetchone()
    conn.close()

    user = User(id=row["id"], username=row["username"], email=row["email"])
    login_user(user)
    flash("Connexion Google réussie.")
    return redirect("/")

@app.route('/user/logout')
def logout_users():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/ajouter_menu', methods=['GET', 'POST'])
def ajouter_menu():
    if request.method == 'POST':
        nom = request.form['nom']
        description = request.form['description']
        prix = float(request.form['prix'])
        categorie = request.form['categorie']
        image_file = request.files['image']

        image_filename = None
        if image_file and allowed_file(image_file.filename):
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            image_filename = filename
        conn = get_db_connction()
        cur = conn.cursor()
        cur.execute("""
                    INSERT INTO menu_items (nom, description, prix, image, categorie)
                    VALUES (%s, %s, %s, %s, %s)
                """, (nom, description, prix, image_filename, categorie))
        conn.commit()
        cur.close()
        conn.close()

        flash("Plat ajouté avec succès !", "success")
        return redirect('/admin/ajouter_menu')
    return render_template('ajouter_menu.html')

@app.route('/form', methods=['GET'])
def formulaire_commande():
    conn = get_db_connction()
    cur = conn.cursor()
    cur.execute("SELECT id, nom, prix FROM menu_items")
    rows = cur.fetchall()

    menu_items = [{'id': row[0], 'nom': row[1], 'prix': row[2]} for row in rows]

    cur.close()
    conn.close()
    return render_template('commande.html', menu_items=menu_items)

#passer une commande
@app.route('/commandes', methods=['POST'])
def passer_commande():
    prenom = request.form['prenom']
    nom = request.form['nom']
    address = request.form['address']
    menu_id = int(request.form['menu'])
    quantite = int(request.form['quantite'])

    conn = get_db_connction()
    cur = conn.cursor()

    # 1. Créer la commande principale
    cur.execute("INSERT INTO commandes (prenom, nom, address, created_at) VALUES (%s, %s, %s, datetime('now'))",
                (prenom, nom, address))
    commande_id = cur.lastrowid

    # 2. Récupérer le prix du menu
    cur.execute("SELECT prix FROM menu_items WHERE id = %s", (menu_id,))
    prix = cur.fetchone()[0]

    # 3. Créer l'item de commande
    cur.execute("INSERT INTO commande_items (commande_id, menu_id, quantite, prix_unitaire) VALUES (%s, %s, %s, %s)",
                (commande_id, menu_id, quantite, prix))

    conn.commit()
    conn.close()
    return render_template('confirmation.html',prenom=prenom, nom=nom, menu_id=menu_id, quantite=quantite, address=address)

@app.route('/commander/<int:menu_id>', methods=['GET', 'POST'])
def passer_commande_directe(menu_id):
    # --- Récupérer les infos du plat ---
    conn = get_db_connction()
    cur = conn.cursor()
    cur.execute("SELECT id, nom, prix FROM menu_items WHERE id = %s", (menu_id,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return "Menu introuvable", 404

    menu = {'id': row[0], 'nom': row[1], 'prix': row[2]}

    #if 'users' not in session:
    if request.method == 'POST':
        if current_user.is_authenticated:
            full_name = current_user.username
            parts = full_name.split(" ")
            prenom = parts[0]
            nom = parts[-1] if len(parts) > 1 else ""
        else:
            prenom = request.form.get('prenom')
            nom = request.form.get('nom')

        adresse = request.form['address']
        tel = request.form['tel']
        quantite = int(request.form['quantite'])
        total = quantite * menu['prix']

        # 1. Créer la commande principale
        cur.execute("""
            INSERT INTO commandes (prenom, nom, address, tel,total, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (prenom, nom, adresse, tel, total, datetime.utcnow()))
        commande_id = cur.lastrowid
        conn.commit()

        # 2. Ajouter l'item de commande
        cur.execute("""
            INSERT INTO commande_items (commande_id, menu_id, quantite, prix_unitaire)
            VALUES (%s, %s, %s, %s)
            """, (commande_id, menu['id'], quantite, menu['prix']))

        conn.commit()
        cur.close()
        conn.close()

        flash("Commande enregistrée avec succès !", "success")
        return redirect(url_for('afficher_menus'))

    #else:
    #    if request.method == 'POST':
    #        prenom = current_user.username.split(' ')[0]
    #        print(prenom)
    #        nom = current_user.username.split(' ')[-1]
    #        print(nom)
    #        adresse = request.form['address']
    #        tel = request.form['tel']
    #        quantite = int(request.form['quantite'])
    #        total = quantite * menu['prix']

    #        cur.execute("""
    #                        INSERT INTO commandes (prenom, nom, address, tel,total, created_at)
    #                        VALUES (?, ?, ?, ?, ?, ?)
    #                    """, (prenom, nom, adresse, tel, total, datetime.utcnow()))
    #        commande_id = cur.lastrowid
    #        conn.commit()

    #        cur.execute("""
    #                        INSERT INTO commande_items (commande_id, menu_id, quantite, prix_unitaire)
    #                        VALUES (?, ?, ?, ?)
    #                    """, (commande_id, menu['id'], quantite, menu['prix']))

    #        conn.commit()
    #        cur.close()
    #        conn.close()

    #        flash("Commande enregistrée avec succès !", "success")
    #        return redirect(url_for('afficher_menus'))

    return render_template('commande_directe.html', menu=menu)

@app.route('/menu')
def afficher_menus():
    categorie = request.args.get('categorie', 'All')  # ex: "Lunch", "Dessert"
    conn = get_db_connction()
    cur = conn.cursor()
    #categorie_norm = normalize_txt(categorie).lower()
    mapping = {
        "Déjeuner": "Dejeuner",
        "Entrer": "Entrer",
        "Dinner": "Dinner",
        "Dessert": "Dessert",
        "Boisson": "Boisson",
        "Végétarien": "Vegetarien"
    }
    categorie_bdd = mapping.get(categorie, categorie)
    if categorie_bdd and categorie_bdd != "All":
        cur.execute("SELECT id, nom, description, prix, image FROM menu_items WHERE lower(categorie) = lower(%s)", (categorie_bdd,))
    else:
        cur.execute("SELECT id, nom, description, prix, image FROM menu_items")

    rows = cur.fetchall()
    cur.close()
    conn.close()

    menu_items = []
    for r in rows:
        image_url = url_for('static', filename=f'uploads/{r[4]}')
        if r[4]:
            menu_items.append({
                'id': r[0],
                'nom': r[1],
                'description': r[2],
                'prix': r[3],
                'image': image_url
                })
    categories = ["All", "Déjeuner", "Entrer", "Dinner", "Dessert", "Boisson", "Végétarien"]

    #return render_template('menus.html', menu_items=menu_items, categorie=categorie or "All")
    return render_template('home.html', menu_items=menu_items, categorie=categorie or "All", categories=categories)

@app.route('/paiement', methods=['GET', 'POST'])
def paiement():
    if request.method == 'POST':
        # On récupère les infos du formulaire
        card_name = request.form['card_name']
        montant = 5000  # Exemple : 5000 FCFA

        # Simulation : 80% de chances que le paiement soit accepté
        paiement_ok = random.random() < 0.8

        if paiement_ok:
            # On simule un ID de transaction
            transaction_id = f"MOCK-{random.randint(100000,999999)}"
            return redirect(url_for('confirmation_paiement',
                                    status="success",
                                    tid=transaction_id,
                                    amount=montant))
        else:
            return redirect(url_for('confirmation_paiement', status="failed"))

    return render_template('paiement.html')

@app.route('/confirmation')
def confirmation_paiement():
    status = request.args.get('status')
    if status == "success":
        tid = request.args.get('tid')
        amount = request.args.get('amount')
        date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        return render_template('confirmation.html',
                               status="success",
                               tid=tid,
                               amount=amount,
                               date=date)
    else:
        return render_template('confirmation.html', status="failed")

init_db()

if __name__ == '__main__':
    app.run(debug=True)
