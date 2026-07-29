from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, StaffProfile

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app

app = create_app()


# ---------- Helpers ----------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if session.get("role") != role:
                flash("Access denied.")
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------- Routes ----------
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]  # "Trekker" or "Trek Staff"

        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
            return redirect(url_for("register"))

        status = "Pending" if role == "Trek Staff" else "Approved"

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            status=status,
        )
        db.session.add(new_user)
        db.session.flush()  # get new_user.id before commit

        if role == "Trek Staff":
            profile = StaffProfile(
                user_id=new_user.id,
                phone=request.form.get("phone", ""),
                experience=request.form.get("experience", ""),
                specialization=request.form.get("specialization", ""),
            )
            db.session.add(profile)

        db.session.commit()
        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            flash("Invalid email or password.")
            return redirect(url_for("login"))

        if user.role == "Trek Staff":
            if user.status == "Pending":
                flash("Your staff account is pending admin approval.")
                return redirect(url_for("login"))
            if user.status == "Blacklisted":
                flash("Your staff account has been blacklisted.")
                return redirect(url_for("login"))

        if user.status == "Blacklisted":
            flash("Your account has been blacklisted.")
            return redirect(url_for("login"))

        session["user_id"] = user.id
        session["name"] = user.name
        session["role"] = user.role

        if user.role == "Admin":
            return redirect(url_for("admin_dashboard"))
        elif user.role == "Trek Staff":
            return redirect(url_for("staff_dashboard"))
        else:
            return redirect(url_for("user_dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/admin/dashboard")
@role_required("Admin")
def admin_dashboard():
    return render_template("admin_dashboard.html", name=session.get("name"))


@app.route("/staff/dashboard")
@role_required("Trek Staff")
def staff_dashboard():
    return render_template("staff_dashboard.html", name=session.get("name"))


@app.route("/user/dashboard")
@role_required("Trekker")
def user_dashboard():
    return render_template("user_dashboard.html", name=session.get("name"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)