import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, flash, g, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet

SECRET_KEY = b'N7JdUOx_E24A81gK5J3dGZgPMZ0XBRFntn2U20r80aM='
cipher = Fernet(SECRET_KEY)


# ── AUTOMATIC COLUMN MIGRATION FOR EXISTING DB ─────────────────────────────────
basedir = os.path.abspath(os.path.dirname(__file__))
db_file = os.path.join(basedir, "database.db")
os.makedirs(os.path.dirname(db_file), exist_ok=True)

conn = sqlite3.connect(db_file)
c = conn.cursor()

# Note: soft-delete
for stmt in [
    "ALTER TABLE note ADD COLUMN is_deleted BOOLEAN DEFAULT 0",
    "ALTER TABLE note ADD COLUMN deleted_at TEXT"
]:
    try:
        c.execute(stmt)
    except sqlite3.OperationalError:
        pass

# User: profile fields
for stmt in [
    "ALTER TABLE user ADD COLUMN info TEXT DEFAULT ''",
    "ALTER TABLE user ADD COLUMN address TEXT DEFAULT ''",
    "ALTER TABLE user ADD COLUMN phone TEXT DEFAULT ''",
    "ALTER TABLE user ADD COLUMN mood TEXT DEFAULT ''"
]:
    try:
        c.execute(stmt)
    except sqlite3.OperationalError:
        pass

      # … setelah ALTER TABLE untuk mood …
try:
    c.execute("ALTER TABLE user ADD COLUMN profile_photo TEXT DEFAULT ''")
except sqlite3.OperationalError:
    pass

for stmt in [
  # … migration sebelumnya …
  "ALTER TABLE user ADD COLUMN cover_photo TEXT DEFAULT ''"
]:
    try: c.execute(stmt)
    except sqlite3.OperationalError: pass

conn.commit()
conn.close()

# ── FLASK APP & DATABASE SETUP ────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "tickie_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_file
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = os.path.join(basedir, "static/uploads")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

db = SQLAlchemy(app)

@app.context_processor
def inject_user():
    return {"user": g.user}

# ── MODELS ─────────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "user"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120), nullable=False)
    email      = db.Column(db.String(120), unique=True, nullable=False)
    password   = db.Column(db.String(200), nullable=False)
    is_admin   = db.Column(db.Boolean, default=False)
    is_active  = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45))
    # profile / biodata
    profile_photo = db.Column(db.String(255), default="")
    cover_photo   = db.Column(db.String(255), default="")

    info       = db.Column(db.Text,   default="")
    address    = db.Column(db.String(255), default="")
    phone      = db.Column(db.String(50),  default="")
    mood       = db.Column(db.Text,   default="")

    notes      = db.relationship("Note", backref="author", lazy=True)
    logs       = db.relationship("LogAktivitas", backref="user", lazy=True)


class Note(db.Model):
    __tablename__ = "note"
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
    __tablename__ = "log_aktivitas"
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"))
    aksi       = db.Column(db.String(200), nullable=False)
    waktu      = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

# ── HOOKS & UTILITIES ─────────────────────────────────────────────────────────
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
        log = LogAktivitas(
            user_id=g.user.id,
            aksi=aksi,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()

# ── USER-FACING ROUTES ─────────────────────────────────────────────────────────
@app.route("/")
def home():
    if not g.user:
        return redirect("/login-page")
    notes = Note.query.filter_by(
        user_id=g.user.id,
        is_deleted=False
    ).order_by(Note.timestamp.desc()).all()

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
        title_raw       = request.form["title"]
        description_raw = request.form["description"]
        category        = request.form.get("category")
        media_file      = request.files.get("media")

        # Enkripsi judul dan deskripsi
        title       = cipher.encrypt(title_raw.encode()).decode()
        description = cipher.encrypt(description_raw.encode()).decode()

        # Proses upload media (jika ada)
        filename = None
        if media_file and media_file.filename != "":
            filename = secure_filename(media_file.filename)
            media_file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        # Tambah catatan ke database
        note = Note(
            title=title,
            description=description,
            category=category,
            media=filename,
            user_id=g.user.id
        )
        db.session.add(note)
        db.session.commit()

        catat_log("Menambahkan catatan terenkripsi")
        flash("Catatan berhasil ditambahkan.", "success")
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
            fname = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
            note.media = fname
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
    flash("Catatan dipindahkan ke Recently Deleted.", "warning")
    return redirect("/")


@app.route("/deleted")
def recently_deleted():
    if not g.user:
        return redirect("/login-page")

    notes = Note.query.filter_by(
        user_id=g.user.id,
        is_deleted=True
    ).order_by(Note.deleted_at.desc()).all()

    for note in notes:
        try:
            note.title = cipher.decrypt(note.title.encode()).decode()
            note.description = cipher.decrypt(note.description.encode()).decode()
        except:
            note.title = "[DEKRIPSI GAGAL]"
            note.description = "[DEKRIPSI GAGAL]"

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
    flash("Catatan dipulihkan.", "success")
    return redirect("/deleted")

@app.route("/destroy/<int:id>")
def destroy_note(id):
    note = Note.query.get_or_404(id)
    if not g.user or note.user_id != g.user.id:
        return redirect("/")
    db.session.delete(note)
    db.session.commit()
    catat_log("Menghapus permanen catatan")
    flash("Catatan dihapus permanen.", "danger")
    return redirect("/deleted")


# ── AUTHENTICATION ─────────────────────────────────────────────────────────────
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
    name  = request.form["signUpName"]
    email = request.form["signUpEmail"].lower()
    pwd   = request.form["signUpPassword"]
    if User.query.filter_by(email=email).first():
        flash("Email sudah terdaftar.")
        return redirect("/register-page")
    user = User(
        name=name,
        email=email,
        password=generate_password_hash(pwd)
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

# ── SETTINGS & PROFILE ─────────────────────────────────────────────────────────
@app.route("/settings", methods=["GET","POST"])
def settings():
    if not g.user:
        return redirect("/login-page")

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        # Validasi dasar
        if not name or not email:
            flash("Nama dan email tidak boleh kosong.")
            return redirect("/settings")

        # Validasi email sederhana
        if "@" not in email or "." not in email:
            flash("Format email tidak valid.")
            return redirect("/settings")

        # Cek jika user ingin ganti password
        if new_password or confirm_password:
            # Wajib isi password lama
            if not current_password:
                flash("Harap masukkan password saat ini untuk mengganti password.")
                return redirect("/settings")

            # Verifikasi password lama
            if not check_password_hash(g.user.password, current_password):
                flash("Password saat ini salah.")
                return redirect("/settings")

            # Minimal panjang password baru
            if len(new_password) < 8:
                flash("Password baru harus minimal 8 karakter.")
                return redirect("/settings")

            # Konfirmasi password
            if new_password != confirm_password:
                flash("Password baru dan konfirmasi tidak cocok.")
                return redirect("/settings")

            # Set password baru
            g.user.password = generate_password_hash(new_password)

        # Update data dasar
        g.user.name = name
        g.user.email = email

        db.session.commit()
        catat_log("Memperbarui profil")
        flash("Profil berhasil diperbarui.")
        return redirect("/settings")

    return render_template("settings.html", user=g.user)


    if request.method == "POST":
        g.user.name  = request.form["name"]
        g.user.email = request.form["email"].lower()
        pwd = request.form.get("password","")
        if pwd:
            g.user.password = generate_password_hash(pwd)
        db.session.commit()
        catat_log("Memperbarui profil dasar")
        flash("Profil dasar diperbarui.")
        return redirect("/settings")

    # ← kirim user ke template
    return render_template("settings.html", user=g.user)

@app.route("/profile", methods=["GET","POST"])
def profile():
    if not g.user: return redirect("/login")
    if request.method=="POST":
        form = request.form.get("form_type")
        if form=="profile":
            g.user.name = request.form["name"]
            g.user.mood = request.form["mood"]
            file = request.files.get("photo")
            if file and file.filename:
                fn = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
                g.user.profile_photo = fn
        db.session.commit()
        return redirect("/profile")
    return render_template("profile_page.html", profile=g.user)


@app.route("/user/<int:id>", methods=["GET","POST"])
def user_profile(id):
    if not g.user: return redirect("/login-page")
    if g.user.id != id: abort(403)

    if request.method == "POST":
        form = request.form.get("form_type")
        file = request.files.get("photo") or request.files.get("cover")
        if form == "photo" and file:
            fn = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
            g.user.profile_photo = fn
            catat_log("Upload avatar")
        elif form == "cover" and file:
            fn = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], fn))
            g.user.cover_photo = fn
            catat_log("Upload cover photo")
        elif form == "bio":
            g.user.info    = request.form.get("info","")
            g.user.phone   = request.form.get("phone","")
            g.user.address = request.form.get("address","")
            g.user.mood    = request.form.get("mood","")
            catat_log("Update biodata")
        db.session.commit()
        flash("Perubahan disimpan.")
        return redirect(f"/user/{id}")

    return render_template("user_profile.html", profile=g.user)
# ── ADMIN PANEL & JSON API ─────────────────────────────────────────────────────
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
def admin_user_list_json():
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    users = User.query.filter_by(is_active=True).order_by(User.name).all()
    return jsonify(users=[{
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "is_admin": u.is_admin
    } for u in users])

@app.route("/admin/user/json/<int:id>")
def admin_user_detail_json(id):
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    u = User.query.get_or_404(id)
    return jsonify({
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "is_admin": u.is_admin,
        "ip_address": u.ip_address,
        "info": u.info,
        "address": u.address,
        "phone": u.phone,
        "mood": u.mood
    })

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
    data = {
        "id": u.id,
        "name": u.name,
        "email": u.email,
        "is_admin": u.is_admin,
        "info": u.info,
        "address": u.address,
        "phone": u.phone,
        "mood": u.mood,
        "notes": [{
            "id": n.id,
            "title": n.title,
            "description": n.description,
            "category": n.category,
            "timestamp": n.timestamp.isoformat()
        } for n in u.notes]
    }
    return jsonify(data)

@app.route("/admin/log/json")
def admin_log_json():
    if not g.user or not g.user.is_admin:
        return jsonify(error="unauthorized"), 403
    logs = LogAktivitas.query.order_by(LogAktivitas.waktu.desc()).limit(100).all()
    return jsonify(logs=[{
        "id": l.id,
        "waktu": l.waktu.strftime("%Y-%m-%d %H:%M"),
        "aksi": l.aksi,
        "user": l.user.name if l.user else "?",
        "ip": l.ip_address or "-"
    } for l in logs])


# ── MAIN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)