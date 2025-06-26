import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# ========== KONFIGURASI ==========
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.secret_key = "rahasia_anda"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ========== MODEL ==========
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    ip_address = db.Column(db.String(45))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)                

class LogAktivitas(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    aksi = db.Column(db.String(200), nullable=False)
    waktu = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    user = db.relationship("User", backref="log_aktivitas")

# ========== FUNGSI LOG ==========
def catat_log(aksi):
    if g.user:
        log = LogAktivitas(
            user_id=g.user.id,
            aksi=aksi,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

# ========== GLOBAL KONTEKS ==========
@app.before_request
def load_current_user():
    user_id = session.get("user_id")
    g.user = User.query.get(user_id) if user_id else None

@app.context_processor
def inject_user():
    return {"user": g.user}

# ========== ROUTES ==========
@app.route("/")
def home():
    notes = Note.query.filter_by(is_deleted=False).all()
    return render_template("view.html", notes=notes)

@app.route("/add", methods=["GET", "POST"])
def add_note():
    if not g.user:
        flash("Silakan login terlebih dahulu.")
        return redirect("/login-page")
    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        note = Note(title=title, description=description)
        db.session.add(note)
        db.session.commit()
        catat_log(f"Menambahkan catatan: {title}")
        flash("Catatan berhasil ditambahkan.")
        return redirect("/")
    return render_template("add.html")

@app.route("/update/<int:id>", methods=["GET", "POST"])
def update_note(id):
    note = Note.query.get_or_404(id)
    if request.method == "POST":
        note.title = request.form["title"]
        note.description = request.form["description"]
        db.session.commit()
        catat_log(f"Memperbarui catatan ID: {id}")
        flash("Catatan berhasil diperbarui.")
        return redirect("/")
    return render_template("update.html", note=note)

@app.route("/delete/<int:id>")
def delete_note(id):
    note = Note.query.get_or_404(id)
    note.is_deleted = True
    note.deleted_at = datetime.utcnow()
    db.session.commit()
    catat_log(f"Soft delete catatan ID: {id}")
    flash("Catatan dipindahkan ke Recently Deleted.")
    return redirect("/")

@app.route("/recently-deleted")
def recently_deleted():
    notes = Note.query.filter_by(is_deleted=True).all()
    return render_template("deleted.html", notes=notes)

@app.route("/restore/<int:id>")
def restore_note(id):
    note = Note.query.get_or_404(id)
    if note.is_deleted:
        note.is_deleted = False
        note.deleted_at = None
        db.session.commit()
        catat_log(f"Restore catatan ID: {id}")
        flash("Catatan berhasil dikembalikan.")
    return redirect("/recently-deleted")

@app.route("/delete-permanent/<int:id>")
def delete_permanent(id):
    note = Note.query.get_or_404(id)
    if note.is_deleted:
        db.session.delete(note)
        db.session.commit()
        flash("Catatan berhasil dihapus secara permanen.")
    else:
        flash("Catatan belum dipindahkan ke Recently Deleted.")
    return redirect("/recently-deleted")

@app.route("/restore-all")
def restore_all():
    notes = Note.query.filter_by(is_deleted=True).all()
    for note in notes:
        note.is_deleted = False
        note.deleted_at = None
    db.session.commit()
    catat_log("Restore semua catatan yang dihapus")
    flash("Semua catatan berhasil dikembalikan.")
    return redirect("/recently-deleted")

@app.route("/delete-permanent-all")
def delete_permanent_all():
    notes = Note.query.filter_by(is_deleted=True).all()
    for note in notes:
        db.session.delete(note)
    db.session.commit()
    catat_log("Delete permanen semua catatan")
    flash("Semua catatan berhasil dihapus permanen.")
    return redirect("/recently-deleted")

# ========== AUTENTIKASI ==========
@app.route("/register", methods=["POST"])
def register():
    name = request.form["signUpName"]
    email = request.form["signUpEmail"].lower()
    password = generate_password_hash(request.form["signUpPassword"])
    if User.query.filter_by(email=email).first():
        flash("Email sudah terdaftar.")
        return redirect("/register-page")
    user = User(name=name, email=email, password=password)
    db.session.add(user)
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
        user.ip_address = request.remote_addr
        db.session.commit()
        catat_log("Login ke sistem")
        flash(f"Halo, {user.name}!")
        return redirect("/")
    flash("Email atau password salah.")
    return redirect("/login-page")

@app.route("/logout")
def logout():
    catat_log("Logout dari sistem")
    session.pop("user_id", None)
    flash("Anda telah logout.")
    return redirect("/")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if not g.user:
        flash("Silakan login terlebih dahulu.")
        return redirect("/login-page")
    if request.method == "POST":
        g.user.name = request.form["name"]
        g.user.email = request.form["email"].lower()
        if request.form["password"]:
            g.user.password = generate_password_hash(request.form["password"])
        db.session.commit()
        catat_log("Mengubah pengaturan profil")
        flash("Pengaturan berhasil diperbarui.")
        return redirect("/settings")
    return render_template("settings.html", user=g.user)

# ========== PANEL ADMIN ==========
@app.route("/admin")
def admin_panel():
    if not g.user or not g.user.is_admin:
        flash("Hanya admin yang dapat mengakses halaman ini.")
        return redirect("/")

    users = User.query.all()
    # Ambil log terakhir tiap user (dalam dict user_id -> log)
    log_terakhir = {
        log.user_id: log
        for log in LogAktivitas.query.order_by(LogAktivitas.waktu.desc()).all()
        if log.user_id not in locals().get("log_terakhir", {})
    }

    return render_template("admin.html", users=users, log_terakhir=log_terakhir)
# ========== JALANKAN ==========
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)