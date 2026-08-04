from datetime import datetime
from models import db, User, StaffProfile, Trek, Booking
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

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
            if user.status == "Deactivated":
                flash("Your staff account has been deactivated.")
                return redirect(url_for("login"))

        if user.status in ("Blacklisted", "Deactivated"):
            flash(f"Your account has been {user.status.lower()}.")
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
    stats = {
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(role="Trekker").count(),
        "total_staff": User.query.filter_by(role="Trek Staff").count(),
        "total_bookings": Booking.query.count(),
    }
    return render_template("admin_dashboard.html", name=session.get("name"), stats=stats)


# ---------- Trek management ----------
@app.route("/admin/treks")
@role_required("Admin")
def admin_treks():
    treks = Trek.query.all()
    return render_template("admin_treks.html", treks=treks)


@app.route("/admin/treks/add", methods=["GET", "POST"])
@role_required("Admin")
def admin_add_trek():
    staff_list = User.query.filter_by(role="Trek Staff", status="Approved").all()

    if request.method == "POST":
        trek = Trek(
            trek_name=request.form["trek_name"],
            location=request.form["location"],
            difficulty=request.form["difficulty"],
            duration=int(request.form["duration"]),
            available_slots=int(request.form["available_slots"]),
            assigned_staff_id=request.form.get("assigned_staff_id") or None,
            status=request.form["status"],
            start_date=datetime.strptime(request.form["start_date"], "%Y-%m-%d").date(),
            end_date=datetime.strptime(request.form["end_date"], "%Y-%m-%d").date(),
        )
        db.session.add(trek)
        db.session.commit()
        flash("Trek created.")
        return redirect(url_for("admin_treks"))

    return render_template("admin_trek_form.html", trek=None, staff_list=staff_list)


@app.route("/admin/treks/edit/<int:trek_id>", methods=["GET", "POST"])
@role_required("Admin")
def admin_edit_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    staff_list = User.query.filter_by(role="Trek Staff", status="Approved").all()

    if request.method == "POST":
        trek.trek_name = request.form["trek_name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.duration = int(request.form["duration"])
        trek.available_slots = int(request.form["available_slots"])
        trek.assigned_staff_id = request.form.get("assigned_staff_id") or None
        trek.status = request.form["status"]
        trek.start_date = datetime.strptime(request.form["start_date"], "%Y-%m-%d").date()
        trek.end_date = datetime.strptime(request.form["end_date"], "%Y-%m-%d").date()
        db.session.commit()
        flash("Trek updated.")
        return redirect(url_for("admin_treks"))

    return render_template("admin_trek_form.html", trek=trek, staff_list=staff_list)


@app.route("/admin/treks/delete/<int:trek_id>", methods=["POST"])
@role_required("Admin")
def admin_delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    db.session.delete(trek)
    db.session.commit()
    flash("Trek deleted.")
    return redirect(url_for("admin_treks"))


# ---------- Staff management ----------
@app.route("/admin/staff")
@role_required("Admin")
def admin_staff():
    staff = User.query.filter_by(role="Trek Staff").all()
    return render_template("admin_staff.html", staff=staff)


@app.route("/admin/staff/status/<int:user_id>/<action>", methods=["POST"])
@role_required("Admin")
def admin_staff_status(user_id, action):
    staff = User.query.get_or_404(user_id)
    if action == "approve":
        staff.status = "Approved"
    elif action == "blacklist":
        staff.status = "Blacklisted"
    elif action == "deactivate":
        staff.status = "Deactivated"
    db.session.commit()
    flash(f"Staff status updated to {staff.status}.")
    return redirect(url_for("admin_staff"))


# ---------- User management ----------
@app.route("/admin/users")
@role_required("Admin")
def admin_users():
    users = User.query.filter_by(role="Trekker").all()
    return render_template("admin_users.html", users=users)


@app.route("/admin/users/status/<int:user_id>/<action>", methods=["POST"])
@role_required("Admin")
def admin_user_status(user_id, action):
    user = User.query.get_or_404(user_id)
    if action == "blacklist":
        user.status = "Blacklisted"
    elif action == "deactivate":
        user.status = "Deactivated"
    elif action == "reactivate":
        user.status = "Approved"
    db.session.commit()
    flash(f"User status updated to {user.status}.")
    return redirect(url_for("admin_users"))


# ---------- Search ----------
@app.route("/admin/search", methods=["GET"])
@role_required("Admin")
def admin_search():
    query = request.args.get("q", "").strip()
    search_type = request.args.get("type", "treks")
    results = []

    if query:
        if search_type == "treks":
            results = Trek.query.filter(
                (Trek.trek_name.ilike(f"%{query}%")) | (Trek.id == query if query.isdigit() else False)
            ).all()
        elif search_type == "staff":
            results = User.query.filter_by(role="Trek Staff").filter(
                (User.name.ilike(f"%{query}%")) | (User.id == query if query.isdigit() else False)
            ).all()
        elif search_type == "users":
            results = User.query.filter_by(role="Trekker").filter(
                (User.name.ilike(f"%{query}%")) | (User.id == query if query.isdigit() else False)
            ).all()

    return render_template("admin_search.html", results=results, query=query, search_type=search_type)


# ---------- Bookings ----------
@app.route("/admin/bookings")
@role_required("Admin")
def admin_bookings():
    bookings = Booking.query.all()
    return render_template("admin_bookings.html", bookings=bookings)

# ---------- Staff: dashboard ----------
@app.route("/staff/dashboard")
@role_required("Trek Staff")
def staff_dashboard():
    treks = Trek.query.filter_by(assigned_staff_id=session["user_id"]).all()
    trek_data = []
    for trek in treks:
        count = Booking.query.filter_by(trek_id=trek.id, booking_status="Booked").count()
        trek_data.append({"trek": trek, "trekker_count": count})
    return render_template("staff_dashboard.html", name=session.get("name"), trek_data=trek_data)


# ---------- Staff: profile ----------
@app.route("/staff/profile", methods=["GET", "POST"])
@role_required("Trek Staff")
def staff_profile():
    user = User.query.get(session["user_id"])
    profile = user.staff_profile

    if request.method == "POST":
        user.name = request.form["name"]
        if profile:
            profile.phone = request.form.get("phone", "")
            profile.experience = request.form.get("experience", "")
            profile.specialization = request.form.get("specialization", "")
        db.session.commit()
        session["name"] = user.name
        flash("Profile updated.")
        return redirect(url_for("staff_profile"))

    return render_template("staff_profile.html", user=user, profile=profile)


# ---------- Staff: trek ownership check ----------
def owns_trek_or_404(trek_id):
    trek = Trek.query.get(trek_id)
    if trek is None:
        flash("That trek doesn't exist.")
        return None
    if trek.assigned_staff_id != session["user_id"]:
        flash("You are not assigned to this trek.")
        return None
    return trek


# ---------- Staff: trek detail, slots/status update, participants ----------
@app.route("/staff/treks/<int:trek_id>", methods=["GET", "POST"])
@role_required("Trek Staff")
def staff_trek_detail(trek_id):
    trek = owns_trek_or_404(trek_id)
    if trek is None:
        return redirect(url_for("staff_dashboard"))

    if request.method == "POST":
        trek.available_slots = int(request.form["available_slots"])
        trek.status = request.form["status"]
        db.session.commit()
        flash("Trek updated.")
        return redirect(url_for("staff_trek_detail", trek_id=trek.id))

    bookings = Booking.query.filter_by(trek_id=trek.id).all()
    return render_template("staff_trek_detail.html", trek=trek, bookings=bookings)


# ---------- Staff: update a participant's booking status ----------
@app.route("/staff/treks/<int:trek_id>/participant/<int:booking_id>/<action>", methods=["POST"])
@role_required("Trek Staff")
def staff_update_participant(trek_id, booking_id, action):
    trek = owns_trek_or_404(trek_id)
    if trek is None:
        return redirect(url_for("staff_dashboard"))

    booking = Booking.query.get_or_404(booking_id)
    if booking.trek_id != trek.id:
        flash("Invalid booking for this trek.")
        return redirect(url_for("staff_trek_detail", trek_id=trek.id))

    if action == "complete":
        booking.booking_status = "Completed"
    elif action == "cancel":
        booking.booking_status = "Cancelled"
    db.session.commit()
    flash("Participant status updated.")
    return redirect(url_for("staff_trek_detail", trek_id=trek.id))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)