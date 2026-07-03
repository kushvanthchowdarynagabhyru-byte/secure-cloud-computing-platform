import re
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from models import db, User, AuditLog

auth_bp = Blueprint("auth", __name__)

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _log(username, action, detail=""):
    entry = AuditLog(
        username=username,
        action=action,
        detail=detail,
        ip_address=request.remote_addr,
    )
    db.session.add(entry)
    db.session.commit()


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not USERNAME_RE.match(username):
            errors.append("Username must be 3-30 characters: letters, numbers, underscores only.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("That username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("That email is already registered.")

        if errors:
            for e in errors:
                flash(e, "error")
            return render_template("register.html", username=username, email=email)

        user = User(username=username, email=email, role="user")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        _log(username, "register", "New account created")

        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("files.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        # Deliberately generic error message to avoid leaking which part was wrong
        if not user or not user.check_password(password):
            _log(username, "login_failed", "Invalid credentials")
            flash("Invalid username or password.", "error")
            return render_template("login.html", username=username)

        login_user(user)
        _log(username, "login_success")
        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for("files.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    _log(current_user.username, "logout")
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.login"))
