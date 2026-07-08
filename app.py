# ============================================================================
# AI Assistance Disclosure (CS50)
#
# ChatGPT (OpenAI) was used as a programming assistant during the development
# of this project. Specifically, it was used to:
#
# • Explain Flask concepts, routing, and application structure.
# • Help debug Python, Flask, HTML, CSS, Jinja, and SQLite errors.
# • Suggest SQL queries for searching, filtering, and displaying data.
# • Help implement the AI scholarship recommendation feature.
# • Help implement user registration, login, logout, and session management.
# • Help implement password hashing using Werkzeug.
# • Help implement the application tracker feature, including status updates
#   and deletion.
# • Help implement scholarship and university detail pages.
# • Help implement the blog feature and article display.
# • Suggest improvements to project structure and code organization.
# • Help improve HTML templates, CSS styling, responsive layout, and UI.
# • Suggest input validation and error handling.
# • Help create the database schema and sample data.
# • Help prepare deployment files including requirements.txt and README.
# • Answer programming questions and explain concepts throughout development.
#
# All code was reviewed, understood, modified where necessary, tested,
# and integrated by the author.
# ============================================================================

from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from cs50 import SQL

app = Flask(__name__)

import secrets
app.secret_key = secrets.token_hex(32)

db = SQL("sqlite:///scholarpath.db")


@app.route("/")
def index():
    return render_template(
        "index.html",
        active_page="home"
    )


@app.route("/scholarships")
def scholarships():

    search = request.args.get("search")
    country = request.args.get("country")

    query = "SELECT * FROM scholarships WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR country LIKE ?)"
        params.append("%" + search + "%")
        params.append("%" + search + "%")

    if country:
        query += " AND country = ?"
        params.append(country)

    scholarships = db.execute(query, *params)

    return render_template(
        "scholarships.html",
        scholarships=scholarships,
        active_page="scholarships"
    )


@app.route("/scholarship/<int:id>")
def scholarship(id):

    scholarship = db.execute(
        "SELECT * FROM scholarships WHERE id = ?",
        id
    )

    if len(scholarship) == 0:
        return "Scholarship not found", 404

    return render_template(
        "scholarship.html",
        scholarship=scholarship[0]
    )

@app.route("/universities")
def universities():

    search = request.args.get("search")

    if search:

        universities = db.execute(
            """
            SELECT *
            FROM universities
            WHERE name LIKE ?
            OR country LIKE ?
            OR ranking LIKE ?
            OR major LIKE ?
            """,
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%",
            "%" + search + "%"
        )

    else:

        universities = db.execute(
            "SELECT * FROM universities"
        )

    return render_template(
        "universities.html",
        universities=universities,
        active_page="universities"
    )

@app.route("/university/<int:id>")
def university(id):

    university = db.execute(
        "SELECT * FROM universities WHERE id = ?",
        id
    )

    if len(university) == 0:
        return "University not found", 404

    return render_template(
        "university.html",
        university=university[0],
        active_page="universities"
        )


@app.route("/ai")
def ai():

    return render_template(
        "ai.html",
        active_page="ai"
    )

@app.route("/recommend", methods=["POST"])
def recommend():

    country = request.form.get("country")

    major = request.form.get("major")

    grade10 = float(request.form.get("grade10"))

    grade12 = float(request.form.get("grade12"))

    ielts = float(request.form.get("ielts"))

    average = (grade10 + grade12) / 2

    scholarships = db.execute(
        """
        SELECT *
        FROM scholarships
        WHERE country = ?
        AND (major = ? OR major = 'All')
        AND min_grade <= ?
        AND min_ielts <= ?
        """,
        country,
        major,
        average,
        ielts
        )

    return render_template(
        "results.html",
        scholarships=scholarships,
        active_page="ai"
        )

@app.route("/tracker")
def tracker():

    if "user_id" not in session:
        return redirect("/login")

    tracker = db.execute(

        """

        SELECT *

        FROM tracker

        WHERE user_id = ?

        """,

        session["user_id"]

        )

    total = len(tracker)

    submitted = len([
        x for x in tracker
        if x["status"] == "Submitted"
        ])

    accepted = len([
        x for x in tracker
        if x["status"] == "Accepted"
        ])

    rejected = len([
        x for x in tracker
        if x["status"] == "Rejected"
        ])

    return render_template(
        "tracker.html",
        tracker=tracker,
        total=total,
        submitted=submitted,
        accepted=accepted,
        rejected=rejected,
        active_page="tracker"
        )

@app.route("/update_status/<int:id>", methods=["POST"])
def update_status(id):

    if "user_id" not in session:
        return redirect("/login")

    status = request.form.get("status")

    db.execute(

        """

        UPDATE tracker

        SET status = ?

        WHERE id = ?

        AND user_id = ?

        """,

        status,

        id,

        session["user_id"]

    )

    return redirect("/tracker")

@app.route("/track/<int:id>", methods=["POST"])
def track(id):

    if "user_id" not in session:
        return redirect("/login")

    scholarship = db.execute(

        "SELECT * FROM scholarships WHERE id=?",

        id

    )

    existing = db.execute(

        """

        SELECT *

        FROM tracker

        WHERE scholarship_id = ?

        AND user_id = ?

        """,

        id,
        session["user_id"]

        )

    if len(existing) > 0:

        return redirect("/tracker")

    db.execute(

        """
        INSERT INTO tracker(

        user_id,

        scholarship_id,

        scholarship_name,

        country,

        deadline,

        status

        )

        VALUES(?,?,?,?,?,?)

        """,

        session["user_id"],
        scholarship[0]["id"],
        scholarship[0]["name"],
        scholarship[0]["country"],
        scholarship[0]["deadline"],
        "Planning"
        )

    return redirect("/tracker")

@app.route("/delete_tracker/<int:id>", methods=["POST"])
def delete_tracker(id):

    if "user_id" not in session:
        return redirect("/login")

    db.execute(

        """
        DELETE FROM tracker

        WHERE id = ?

        AND user_id = ?

        """,

        id,
        session["user_id"]

    )

    return redirect("/tracker")


@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "GET":

        return render_template(
            "register.html"
        )

    username = request.form.get("username")

    password = request.form.get("password")

    confirmation = request.form.get("confirmation")

    if password != confirmation:

        return "Passwords don't match"

    existing = db.execute(
        "SELECT * FROM users WHERE username = ?",
        username
        )

    if len(existing) > 0:
        return "Username already exists"

    hash = generate_password_hash(password)

    db.execute(

        """
        INSERT INTO users(username,hash)
        VALUES(?,?)
        """,

        username,

        hash

    )

    return redirect("/login")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    session.clear()

    username = request.form.get("username")

    password = request.form.get("password")

    rows = db.execute(

        """
        SELECT *
        FROM users
        WHERE username=?
        """,

        username

    )

    if len(rows) != 1:

        return "Invalid username"

    if not check_password_hash(

        rows[0]["hash"],

        password

    ):

        return render_template(
            "login.html",
            error="Invalid password"
            )

    session["user_id"] = rows[0]["id"]

    return redirect("/")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

@app.route("/blog")
def blog():

    articles = db.execute(
        "SELECT * FROM blog ORDER BY id DESC"
    )

    return render_template(
        "blog.html",
        articles=articles,
        active_page="blog"
    )

@app.route("/blog/<int:id>")
def article(id):

    article = db.execute(
        "SELECT * FROM blog WHERE id=?",
        id
    )

    if len(article) == 0:
        return "Article not found",404

    return render_template(
        "article.html",
        article=article[0]
    )

if __name__ == "__main__":
    app.run(debug=True)


