from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            firstname TEXT,
            lastname TEXT,
            email TEXT,
            address TEXT,
            filename TEXT,
            word_count INTEGER
        )
    """)
    conn.commit()
    conn.close()


init_db()


@app.route("/")
def index():
    """Registration page (4a + 4b + 4e upload button)."""
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form["username"].strip()
    password = request.form["password"]
    firstname = request.form.get("firstname", "")
    lastname = request.form.get("lastname", "")
    email = request.form.get("email", "")
    address = request.form.get("address", "")

    uploaded_file = request.files.get("userfile")
    filename = None
    word_count = 0

    if uploaded_file and uploaded_file.filename:
        filename = f"{username}_{uploaded_file.filename}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        uploaded_file.save(save_path)

        with open(save_path, "r", errors="ignore") as f:
            content = f.read()
        word_count = len(content.split())

    conn = get_db()
    c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO users
               (username, password, firstname, lastname, email, address, filename, word_count)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, password, firstname, lastname, email, address, filename, word_count),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return "Username already exists. <a href='/'>Go back</a>", 400
    conn.close()

    return redirect(url_for("profile", username=username))


@app.route("/login", methods=["GET", "POST"])
def login():
    """Re-login page (4d): username + password -> retrieve stored info."""
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"].strip()
    password = request.form["password"]

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = c.fetchone()
    conn.close()

    if user is None:
        return render_template("login.html", error="Invalid username or password.")

    return redirect(url_for("profile", username=username))


@app.route("/profile/<username>")
def profile(username):
    """Display page (4c): shows the info from 4b + word count + download button."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if user is None:
        return "User not found.", 404

    return render_template("profile.html", user=user)


@app.route("/download/<username>")
def download(username):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT filename FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row is None or row["filename"] is None:
        return "No file on record for this user.", 404

    return send_from_directory(app.config["UPLOAD_FOLDER"], row["filename"], as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
