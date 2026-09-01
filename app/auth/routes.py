import re

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("main.account"))
        return render_template("login.html")

    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        flash("Wrong username or password.", "login_error")
        return redirect(url_for("auth.login"))

    login_user(user)
    return redirect(url_for("main.account"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if current_user.is_authenticated:
            return redirect(url_for("main.account"))
        return render_template("register.html")

    full_name = request.form.get("full_name", "").strip()
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")

    errors = []
    if not full_name:
        errors.append("Enter your name.")
    if not re.match(r"^[a-z0-9_]{3,20}$", username):
        errors.append("Username must be 3-20 lowercase letters, numbers, or underscores.")
    if len(password) < 6:
        errors.append("Password must be at least 6 characters.")
    if confirm != password:
        errors.append("Passwords don't match.")
    if username and User.query.filter_by(username=username).first():
        errors.append("That username is taken. Try another.")

    if errors:
        for e in errors:
            flash(e, "register_error")
        return redirect(url_for("auth.register"))

    user = User(username=username, full_name=full_name)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash("Account created. Welcome!", "success")
    return redirect(url_for("main.account"))


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))
