import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

# ── Pastikan kolom is_deleted & deleted_at ada di SQLite ───────────────────────
basedir = os.path.abspath(os.path.dirname(__file__))
db_file = os.path.join(basedir, "database.db")
os.makedirs(os.path.dirname(db_file), exist_ok=True)

conn = sqlite3.connect(db_file)
c = conn.cursor()
try:
    c.execute("ALTER TABLE note ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
except sqlite3.OperationalError:
    pass
try:
    c.execute("ALTER TABLE note ADD COLUMN deleted_at TEXT")
except sqlite3.OperationalError:
    pass
conn.commit()
conn.close()

# ── Flask app & DB setup ────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "tickie_secret_key"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "static", "uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)

# ── Models ─────────────────────────────────────────────────────────────────────
class User(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    is_admin   = db.Column(db.Boolean, default=False)
    is_active  = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45))
    notes      = db.relationship("Note", backref="author", lazy=True)
    logs       = db.relationship("LogAktivitas", backref="user", lazy=True)

class Note(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category    = db.Column(db.String(100))
    media       = db.Column(db.String(255))
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)
    is_deleted  = db.Column(db.Boolean, default=False)
    deleted_at  = db.Column(db.DateTime)
    user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class LogAktivitas(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"))
    aksi       = db.Column(db.String(200), nullable=False)
    waktu      = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

# ── Hooks & Utilities ──────────────────────────────────────────────────────────
@app.before_request
def load_user():
    g.user = None
    uid = session.get("user_id")
    if uid:
        g.user = User.query.get(uid)

@app.context_processor
def inject_user():
    return {"user": g.user}

def catat_log(aksi):
    if g.user:
        log = LogAktivitas(user_id=g.user.id, aksi=aksi, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()

# ── Routes: User CRUD & Soft-Delete ─────────────────────────────────────────────
@app.route("/")
def home():
    if not g.user:
        return redirect("/login-page")
    notes = Note.query.filter_by(user_id=g.user.id, is_deleted=False).order_by(Note.timestamp.desc()).all()
    return render_template("view.html", notes=notes)

@app.route("/add", methods=["GET", "POST"])
def add_note():
    if not g.user:
        return redirect("/login-page")
    if request.method == "POST":
        file = request.files.get("media")
        filename = None
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        note = Note(
            title=request.form["title"],
            description=request.form["description"],
            category=request.form.get("category"),
            media=filename,
            user_id=g.user.id
        )
        db.session.add(note)
        db.session.commit()
        catat_log("Menambahkan catatan")
        flash("Catatan berhasil ditambahkan.")
        return redirect("/")
    return render_template("add.html")

@app.route("/update/<int:id>", methods=["GET", "POST"])
def update_note(id):
    note = Note.query.get_or_404(id)
    if not g.user or note.user_id != g.user.id:
        return redirect("/")
    if request.method == "POST":
        note.title       = request.form["title"]
        note.description = request.form["description"]
        note.category    = request.form.get("category")
        file = request.files.get("media")
        if file and file.filename:
            fn = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
            note.media = fn
        db.session.commit()
        catat_log("Memperbarui catatan")
        flash("Catatan diperbarui.")
        return redirect("/")
    return render_template("update.html", note=note)

@app.route("/delete/<int:id>")
def soft_delete_note(id):
    note = Note.query.get_or_404(id)
    if not g.user or note.user_id != g.user.id:
        return redirect("/")
    note.is_deleted = True
    note.deleted_at = datetime.utcnow()
    db.session.commit()
    catat_log("Soft delete catatan")
    flash("Catatan dipindahkan ke Recently Deleted.")
    return redirect("/")

@app.route("/deleted")
def recently_deleted():
    if not g.user:
        return redirect("/login-page")
    notes = Note.query.filter_by(user_id=g.user.id, is_deleted=True).order_by(Note.deleted_at.desc()).all()
    return render_template("deleted.html", notes=notes)

@app.route("/restore/<int:id>")
def restore_note(id):
    note = Note.query.get_or_404(id)
    if not g.user or note.user_id != g.user.id:
        return redirect("/")
    note.is_deleted = False
    note.deleted_at = None
    db.session.commit()
    catat_log("Memulihkan catatan")
    flash("Catatan dipulihkan.")
    return redirect("/deleted")

@app.route("/destroy/<int:id>")
def destroy_note(id):
    note = Note.query.get_or_404(id)
    if not g.user or note.user_id != g.user.id:
        return redirect("/")
    db.session.delete(note)
    db.session.commit()
    catat_log("Hapus permanen catatan")
    flash("Catatan dihapus permanen.")
    return redirect("/deleted")

# ── Routes: Authentikasi ─────────────────────────────────────────────────────────
@app.route("/login-page")
def login_page():
    return render_template("login.html")

@app.route("/register-page")
def register_page():
    return render_template("register.html")

@app.route("/login", methods=["POST"])
def login():
    email = request.form["loginEmail"].lower()
    pwd   = request.form["loginPassword"]
    user  = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, pwd):
        session["user_id"] = user.id
        user.ip_address = request.remote_addr
        db.session.commit()
        catat_log("Login")
        return redirect("/")
    flash("Email atau password salah.")
    return redirect("/login-page")

@app.route("/register", methods=["POST"])
def register():
    email = request.form["signUpEmail"].lower()
    if User.query.filter_by(email=email).first():
        flash("Email sudah terdaftar.")
        return redirect("/register-page")
    user = User(
        name     = request.form["signUpName"],
        email    = email,
        password = generate_password_hash(request.form["signUpPassword"])
    )
    db.session.add(user)
    db.session.commit()
    flash("Registrasi berhasil.")
    return redirect("/login-page")

@app.route("/logout")
def logout():
    catat_log("Logout")
    session.clear()
    return redirect("/login-page")

# ── Routes: Admin & JSON API ────────────────────────────────────────────────────
@app.route("/admin")
def admin_panel():
    if not g.user or not g.user.is_admin:
        return redirect("/")
    stats = {
        "user_count": User.query.filter_by(is_active=True).count(),
        "note_count": Note.query.filter_by(is_deleted=False).count(),
        "log_count":  LogAktivitas.query.count()
    }
    return render_template("admin.html", **stats)

@app.route("/admin/user/json/all")
def admin_user_list():
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    return jsonify(users=[{"id":u.id,"name":u.name,"email":u.email,"is_admin":u.is_admin} for u in users])

@app.route("/admin/user/json/<int:id>")
def admin_user_detail(id):
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    u = User.query.get_or_404(id)
    return jsonify(id=u.id, name=u.name, email=u.email, is_admin=u.is_admin, ip_address=u.ip_address)

@app.route("/admin/user/<int:id>/delete", methods=["POST"])
def admin_user_delete(id):
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    u = User.query.get_or_404(id)
    if u.id == g.user.id:
        return jsonify(error="cannot delete yourself"), 400
    u.is_active = False
    db.session.commit()
    catat_log(f"Menonaktifkan akun {u.email}")
    return jsonify(status="ok")

@app.route("/admin/user/<int:id>/restore", methods=["POST"])
def admin_user_restore(id):
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    u = User.query.get_or_404(id)
    u.is_active = True
    db.session.commit()
    catat_log(f"Memulihkan akun {u.email}")
    return jsonify(status="ok")

@app.route("/admin/user/<int:id>/backup")
def admin_user_backup(id):
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    u = User.query.get_or_404(id)
    data = {"id":u.id,"name":u.name,"email":u.email,"is_admin":u.is_admin,
            "notes":[{"id":n.id,"title":n.title,"description":n.description,
                      "category":n.category,"timestamp":n.timestamp.isoformat()}
                     for n in u.notes]}
    return jsonify(data)

@app.route("/admin/log/json")
def admin_log_json():
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    logs = LogAktivitas.query.order_by(LogAktivitas.waktu.desc()).limit(100).all()
    return jsonify(logs=[{"id":l.id,"waktu":l.waktu.strftime("%Y-%m-%d %H:%M"),
                          "aksi":l.aksi,"user":l.user.name if l.user else "?","ip":l.ip_address}
                         for l in logs])

# ── Jalankan ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)