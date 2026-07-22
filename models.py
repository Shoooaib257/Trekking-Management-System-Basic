from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # hashed
    role = db.Column(db.String(20), nullable=False)  # Admin / Trek Staff / Trekker
    status = db.Column(db.String(20), default="Pending")  # Pending / Approved / Blacklisted

    # 1:1 with StaffProfile
    staff_profile = db.relationship("StaffProfile", backref="user", uselist=False, cascade="all, delete-orphan")

    # 1:M as a trekker's bookings
    bookings = db.relationship("Booking", backref="user", lazy=True, foreign_keys="Booking.user_id")

    # 1:M treks assigned to this user (as staff)
    assigned_treks = db.relationship("Trek", backref="assigned_staff", lazy=True, foreign_keys="Trek.assigned_staff_id")


class StaffProfile(db.Model):
    __tablename__ = "staff_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    experience = db.Column(db.String(100))
    specialization = db.Column(db.String(100))


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    difficulty = db.Column(db.String(20))  # Easy / Moderate / Hard
    duration = db.Column(db.Integer)  # in days
    available_slots = db.Column(db.Integer, default=0)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(20), default="Pending")  # Pending/Approved/Open/Closed/Completed
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)

    bookings = db.relationship("Booking", backref="trek", lazy=True)


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)
    booking_date = db.Column(db.DateTime, default=db.func.now())
    booking_status = db.Column(db.String(20), default="Booked")  # Booked/Cancelled/Completed
    payment_status = db.Column(db.String(20), default="Pending")