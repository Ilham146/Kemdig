from datetime import datetime
from app import db

class User(db.Model): 
    """Model untuk pengguna aplikasi."""
    _tablename_ = "user"
    
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(120), nullable=False)
    email       = db.Column(db.String(120), unique=True, nullable=False)
    password    = db.Column(db.String(200), nullable=False)
    is_admin    = db.Column(db.Boolean, default=False)
    is_active   = db.Column(db.Boolean, default=True)
    ip_address  = db.Column(db.String(45))

    # Biodata tambahan (untuk halaman profil)
    info        = db.Column(db.Text, default="")
    address     = db.Column(db.String(255), default="")
    phone       = db.Column(db.String(50), default="")
    mood        = db.Column(db.Text, default="")
    profile_photo = db.Column(db.String(255), default="")
    cover_photo   = db.Column(db.String(255), default="")

    # Relasi
    notes       = db.relationship("Note", backref="author", lazy=True)
    logs        = db.relationship("LogAktivitas", backref="user", lazy=True)

    def _repr_(self):
        return f"<User {self.id} – {self.email}>"

class Note(db.Model):
    """Model untuk catatan pengguna."""
    _tablename_ = "note"
    
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category    = db.Column(db.String(100))
    media       = db.Column(db.String(255))
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)

    # Soft-delete
    is_deleted  = db.Column(db.Boolean, default=False)
    deleted_at  = db.Column(db.DateTime)

    user_id     = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def _repr_(self):
        return f"<Note {self.id} – {self.title}>"

class LogAktivitas(db.Model):
    """Model untuk mencatat aktivitas pengguna."""
    _tablename_ = "log_aktivitas"
    
    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("user.id"))
    aksi       = db.Column(db.String(200), nullable=False)
    waktu      = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

    def _repr_(self):
        return f"<Log {self.id} – {self.aksi} @ {self.waktu}>"