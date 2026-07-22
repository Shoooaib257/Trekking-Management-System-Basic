from werkzeug.security import generate_password_hash
from app import app
from models import db, User

ADMIN_EMAIL = "admin@trek.com"
ADMIN_PASSWORD = "admin123"

with app.app_context():
    db.create_all()

    existing = User.query.filter_by(email=ADMIN_EMAIL).first()
    if not existing:
        admin = User(
            name="Admin",
            email=ADMIN_EMAIL,
            password=generate_password_hash(ADMIN_PASSWORD),
            role="Admin",
            status="Approved",
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")
    else:
        print("Admin user already exists.")