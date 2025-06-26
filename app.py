import os
from flask import Flask, render_template, request, redirect, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ===================== Inisialisasi =====================
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = "rahasia_anda"  # Ganti dengan secret key aman!

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ===================== MODEL =====================

class database_model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(200), nullable=False)

    def __init__(self, title, description):
        self.title = title
        self.description = description

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ===================== KONTEKS & OTENTIKASI =====================

@app.before_request
def load_current_user():
    if "user_id" in session:
        g.user = User.query.get(session["user_id"])
    else:
        g.user = None

@app.context_processor
def inject_user():
    return {"user": g.user}

# ===================== ROUTES UTAMA =====================

@app.route("/")
def home():
    all_records = database_model.query.all()
    return render_template("view.html", all_records=all_records)

@app.route("/add", methods=["GET", "POST"])
def add():
    if not g.user:
        flash("Anda harus login terlebih dahulu.")
        return redirect("/")
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        entry = database_model(title, description)
        db.session.add(entry)
        db.session.commit()
        flash("Data berhasil ditambahkan.")
        return redirect("/")
    return render_template("add.html")

@app.route("/update/<int:id>", methods=["GET", "POST"])
def update(id):
    if not g.user:
        flash("Login diperlukan untuk mengedit data.")
        return redirect("/")
    item = database_model.query.get_or_404(id)
    if request.method == "POST":
        item.title = request.form["title"]
        item.description = request.form["description"]
        db.session.commit()
        flash("Data berhasil diperbarui.")
        return redirect("/")
    return render_template("update.html", Item=item)

@app.route("/delete/<int:id>")
def delete(id):
    if not g.user:
        flash("Login diperlukan untuk menghapus data.")
        return redirect("/")
    item = database_model.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    flash("Data berhasil dihapus.")
    return redirect("/")

# ===================== LOGIN / REGISTER =====================

@app.route("/register", methods=["POST"])
def register():
    name = request.form["signUpName"]
    email = request.form["signUpEmail"].lower()
    password = generate_password_hash(request.form["signUpPassword"])

    if User.query.filter_by(email=email).first():
        flash("Email sudah terdaftar.")
        return redirect("/register-page")

    new_user = User(name=name, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    flash("Registrasi berhasil. Silakan login.")
    return redirect("/login-page")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["loginEmail"].lower()
    password = request.form["loginPassword"]
    user = User.query.filter_by(email=email).first()

    if user and check_password_hash(user.password, password):
        session["user_id"] = user.id
        flash(f"Selamat datang, {user.name}!")
        return redirect("/")
    flash("Email atau password salah.")
    return redirect("/login-page")

@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Anda telah logout.")
    return redirect("/")

# ===================== HALAMAN TAMBAHAN =====================

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not g.user:
        flash("Anda harus login dulu.")
        return redirect("/login-page")
    
    if request.method == "POST":
        g.user.name = request.form["name"]
        g.user.email = request.form["email"].lower()
        if request.form["password"]:
            g.user.password = generate_password_hash(request.form["password"])
        db.session.commit()
        flash("Pengaturan berhasil diperbarui.")
        return redirect("/settings")
    
    return render_template("settings.html", user=g.user)

# ===================== JALANKAN APLIKASI =====================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)