# # Trekking Management Application

A Flask-based web app for managing trekking activities across three roles: Admin, Trek Staff, and Trekker (User).

## Tech Stack
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja2 + HTML + CSS (no Bootstrap, no JavaScript)

## Project Structure

project/
├── app.py
├── models.py
├── config.py
├── seed_admin.py
├── requirements.txt
├── templates/
└── static/
└── style.css

## Setup Instructions

1. **Clone/extract the project folder** and navigate into it:
```bash
   cd project
```

2. **Create and activate a virtual environment** (recommended):
```bash
   python3 -m venv venv
   source venv/bin/activate      # Mac/Linux
   venv\Scripts\activate         # Windows
```

3. **Install dependencies:**
```bash
   pip install -r requirements.txt
```

4. **Create the database** (creates `trekking.db` with all tables):
```bash
   python3 app.py
```
   Press `Ctrl+C` once it starts running — this step just needs the tables created.

5. **Seed the Admin account:**
```bash
   python3 seed_admin.py
```
   Creates the pre-existing Admin login:
   - Email: `admin@trek.com`
   - Password: `admin123`

6. **Run the app:**
```bash
   python3 app.py
```
   Visit `http://127.0.0.1:5000` in your browser.

## Roles & Access

- **Admin** — pre-seeded, no registration. Manages treks, staff, users, bookings, and search.
- **Trek Staff** — registers via `/register`, needs Admin approval before login is allowed. Manages assigned treks and participants.
- **Trekker (User)** — registers via `/register`, can browse/filter/book open treks and view booking history.

## Testing the App

1. Log in as Admin (`admin@trek.com` / `admin123`).
2. Register a couple of Trek Staff and Trekker accounts from `/register`.
3. As Admin, approve the new staff and assign them to a trek you create.
4. As the approved staff member, log in and update trek slots/status.
5. As a trekker, browse open treks, filter by difficulty/location, and book one.
6. Check the Admin's Bookings page and the trekker's dashboard to confirm the booking appears in both places.

## Notes
- The database is created programmatically via `db.create_all()` — no manual DB tools used.
- Passwords are hashed with Werkzeug before storage.
- Deleting `trekking.db` and re-running steps 4–5 resets the app to a clean state.