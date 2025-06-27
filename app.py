import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet

SECRET_KEY = b'N7JdUOx_E24A81gK5J3dGZgPMZ0XBRFntn2U20r80aM='
cipher = Fernet(SECRET_KEY)

app = Flask(__name__)
app.secret_key = "tickie_secret"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)

# =================== MODELS ===================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))
    notes = db.relationship("Note", backref="author", lazy=True)
    logs = db.relationship("LogAktivitas", backref="user", lazy=True)
    is_active = db.Column(db.Boolean, default=True)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    media = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class LogAktivitas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    aksi = db.Column(db.String(200), nullable=False)
    waktu = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

# =================== UTILITAS ===================

@app.before_request
def load_user():
    g.user = User.query.get(session.get("user_id")) if session.get("user_id") else None

@app.context_processor
def inject_user():
    return {"user": g.user}

def catat_log(aksi):
    if g.user:
        db.session.add(LogAktivitas(user_id=g.user.id, aksi=aksi, ip_address=request.remote_addr))
        db.session.commit()

# =================== ROUTES ===================

@app.route("/")
def home():
    if not g.user:
        flash("Silakan login terlebih dahulu.")
        return redirect("/login-page")
    notes = Note.query.filter_by(user_id=g.user.id).order_by(Note.timestamp.desc()).all()

    for note in notes:
        try:
            note.title = cipher.decrypt(note.title.encode()).decode()
            note.description = cipher.decrypt(note.description.encode()).decode()
        except:
            note.title = "[DEKRIPSI GAGAL]"
            note.description = "[DEKRIPSI GAGAL]"

    return render_template("view.html", notes=notes)


@app.route("/add", methods=["GET", "POST"])
def add_note():
    if not g.user:
        return redirect("/login-page")
    if request.method == "POST":
        title_raw = request.form["title"]
        description_raw = request.form["description"]
        category = request.form.get("category")
        media_file = request.files.get("media")

        title = cipher.encrypt(title_raw.encode()).decode()
        description = cipher.encrypt(description_raw.encode()).decode()

        filename = None
        if media_file and media_file.filename != "":
            filename = secure_filename(media_file.filename)
            media_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        db.session.add(Note(
            title=title, description=description,
            category=category, media=filename,
            user_id=g.user.id
        ))
        db.session.commit()
        catat_log("Menambahkan catatan terenkripsi")
        flash("Catatan berhasil ditambahkan.")
        return redirect("/")
    return render_template("add.html")


@app.route("/update/<int:id>", methods=["GET", "POST"])
def update_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != g.user.id:
        flash("Tidak diizinkan.")
        return redirect("/")
    if request.method == "POST":
        note.title = request.form["title"]
        note.description = request.form["description"]
        note.category = request.form.get("category")

        media_file = request.files.get("media")
        if media_file and media_file.filename != "":
            filename = secure_filename(media_file.filename)
            media_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            note.media = filename

        db.session.commit()
        catat_log("Memperbarui catatan")
        flash("Catatan diperbarui.")
        return redirect("/")
    return render_template("update.html", note=note)

@app.route("/delete/<int:id>")
def delete_note(id):
    note = Note.query.get_or_404(id)
    if note.user_id != g.user.id:
        flash("Tidak diizinkan.")
        return redirect("/")
    db.session.delete(note)
    db.session.commit()
    catat_log("Menghapus catatan")
    flash("Catatan berhasil dihapus.")
    return redirect("/")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["loginEmail"].lower()
    password = request.form["loginPassword"]
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        session["user_id"] = user.id
        user.ip_address = request.remote_addr
        db.session.commit()
        catat_log("Login")
        flash(f"Selamat datang, {user.name}!")
        return redirect("/")
    flash("Login gagal.")
    return redirect("/login-page")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["signUpName"]
    email = request.form["signUpEmail"].lower()
    password = generate_password_hash(request.form["signUpPassword"])
    if User.query.filter_by(email=email).first():
        flash("Email sudah digunakan.")
        return redirect("/register-page")
    db.session.add(User(name=name, email=email, password=password))
    db.session.commit()
    flash("Registrasi berhasil.")
    return redirect("/login-page")

@app.route("/logout")
def logout():
    catat_log("Logout")
    session.clear()
    flash("Logout berhasil.")
    return redirect("/login-page")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not g.user:
        return redirect("/login-page")
    if request.method == "POST":
        g.user.name = request.form["name"]
        g.user.email = request.form["email"].lower()
        if request.form["password"]:
            g.user.password = generate_password_hash(request.form["password"])
        db.session.commit()
        catat_log("Memperbarui profil")
        flash("Profil diperbarui.")
        return redirect("/settings")
    return render_template("settings.html")

@app.route("/admin")
def admin_panel():
    if not g.user or not g.user.is_admin:
        flash("Hanya admin yang dapat mengakses.")
        return redirect("/")
    return render_template("admin.html",
        user_count=User.query.count(),
        note_count=Note.query.count(),
        log_count=LogAktivitas.query.count()
    )

@app.route("/admin/user/json/all")
def admin_user_list_json():
    if not g.user or not g.user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    users = User.query.filter_by(is_active=True).order_by(User.name.asc()).all()
    return jsonify({
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "is_admin": u.is_admin
            }
            for u in users
        ]
    })

@app.route("/admin/user/json/<int:id>")
def admin_user_json(id):
    if not g.user or not g.user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    u = User.query.get_or_404(id)
    return jsonify({
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "is_admin": u.is_admin,
        "ip_address": u.ip_address
    })

@app.route("/admin/log/json")
def admin_log_json():
    if not g.user or not g.user.is_admin:
        return jsonify({"error": "Unauthorized"}), 403
    logs = LogAktivitas.query.order_by(LogAktivitas.waktu.desc()).limit(100).all()
    return jsonify({
        "logs": [
            {
                "id": log.id,
                "waktu": log.waktu.strftime("%Y-%m-%d %H:%M"),
                "aksi": log.aksi,
                "ip": log.ip_address or "–",
                "user": log.user.name if log.user else "?"
            }
            for log in logs
        ]
    })

@app.route("/admin/user/<int:id>/delete", methods=["POST"])
def admin_delete_user(id):
    if not g.user or not g.user.is_admin:
        return "", 403
    user = User.query.get_or_404(id)
    if user.id == g.user.id:
        return "Admin tidak dapat menghapus dirinya sendiri.", 400
    user.is_active = False
    db.session.commit()
    catat_log(f"Menonaktifkan akun {user.name}")
    return "OK"

@app.route("/admin/user/<int:id>/restore", methods=["POST"])
def admin_restore_user(id):
    if not g.user or not g.user.is_admin:
        return "", 403
    user = User.query.get_or_404(id)
    user.is_active = True
    db.session.commit()
    catat_log(f"Memulihkan akun {user.name}")
    return "OK"

@app.route("/admin/user/<int:id>/backup")
def admin_backup_user(id):
    if not g.user or not g.user.is_admin:
        return "", 403
    user = User.query.get_or_404(id)
    return jsonify({
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": user.is_admin,
            "notes": [
                {
                    "id": n.id,
                    "title": n.title,
                    "description": n.description,
                    "category": n.category,
                    "created": n.timestamp.strftime("%Y-%m-%d %H:%M")
                } for n in user.notes
            ]
        }
    })

# =================== RUN ===================

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)