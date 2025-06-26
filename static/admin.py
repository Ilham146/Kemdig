from app import app, db, User

with app.app_context():
    user = User.query.filter_by(email="ilham@gmail.com").first()
    if user:
        user.is_admin = True
        db.session.commit()
        print("✅ ilham@gmail.com sekarang adalah admin.")
    else:
        print("⚠️ User dengan email tersebut belum terdaftar.")