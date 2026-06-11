"""Authentication: email/password and Google OAuth (via Authlib)."""
from flask import Blueprint, request, redirect, url_for, render_template, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models.models import SessionLocal, User
import os

auth = Blueprint("auth", __name__)


# ── Email / Password ──────────────────────────────────────────────────────────

@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("api.index"))
    if request.method == "GET":
        return render_template("signup.html")

    email = (request.form.get("email") or "").strip().lower()
    name = (request.form.get("name") or "").strip()
    password = request.form.get("password") or ""

    if not email or not password:
        flash("Email and password are required.")
        return redirect(url_for("auth.signup"))
    if len(password) < 8:
        flash("Password must be at least 8 characters.")
        return redirect(url_for("auth.signup"))

    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            flash("An account with that email already exists. Try logging in.")
            return redirect(url_for("auth.login"))
        user = User(email=email, name=name or email.split("@")[0])
        user.set_password(password)
        db.add(user)
        db.commit()
        db.refresh(user)
        login_user(user)
    finally:
        db.close()
    return redirect(url_for("api.index"))


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("api.index"))
    if request.method == "GET":
        return render_template("login.html")

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.")
            return redirect(url_for("auth.login"))
        login_user(user)
    finally:
        db.close()
    return redirect(url_for("api.index"))


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


# ── Google OAuth ──────────────────────────────────────────────────────────────

@auth.route("/login/google")
def login_google():
    oauth = current_app.extensions["authlib.integrations.flask_client"]
    redirect_uri = url_for("auth.google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth.route("/login/google/callback")
def google_callback():
    oauth = current_app.extensions["authlib.integrations.flask_client"]
    token = oauth.google.authorize_access_token()
    info = token.get("userinfo") or oauth.google.userinfo()

    google_id = info.get("sub")
    email = (info.get("email") or "").strip().lower()
    name = info.get("name")
    avatar = info.get("picture")

    if not email:
        flash("Google did not return an email address.")
        return redirect(url_for("auth.login"))

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.google_id == google_id).first()
        if not user:
            user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
            if avatar:
                user.avatar_url = avatar
            if not user.name and name:
                user.name = name
        else:
            user = User(email=email, name=name, google_id=google_id, avatar_url=avatar)
            db.add(user)
        db.commit()
        db.refresh(user)
        login_user(user)
    finally:
        db.close()
    return redirect(url_for("api.index"))