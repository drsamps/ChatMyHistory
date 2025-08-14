from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from ...extensions import db
from ...models.user import User


auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = User.query.filter_by(email=email).first()
    
    if not user:
        flash("Invalid credentials", "danger")
        return redirect(url_for("auth.login"))
    
    stored = user.password_hash
    is_blank = (not stored) or (isinstance(stored, str) and stored.strip() == "")
    looks_like_bcrypt = isinstance(stored, str) and stored.startswith("$2") and len(stored) > 20
    equals_plain = isinstance(stored, str) and stored == password
    equals_plain_stripped = (
        isinstance(stored, str)
        and not looks_like_bcrypt
        and isinstance(password, str)
        and stored
        and password
        and stored.strip() == password.strip()
    )

    # If user exists but has no password set, route to set-password
    if is_blank:
        session["pending_password_user_id"] = user.id
        flash("Please set a new password to continue.", "info")
        return redirect(url_for("auth.set_password"))
    
    # Check if the stored password_hash is actually a plaintext password
    # This handles migration from plaintext to hashed passwords
    if isinstance(stored, str):
        # Fast-path exact match
        if equals_plain:
            user.set_password(password)
            db.session.commit()
            flash("Your password has been automatically updated for security.", "info")
            login_user(user)
            return redirect(url_for("index"))
        # If the stored value doesn't look like a bcrypt hash, try a lenient comparison
        if not looks_like_bcrypt and equals_plain_stripped:
            user.set_password(password)
            db.session.commit()
            flash("Your password has been automatically updated for security.", "info")
            login_user(user)
            return redirect(url_for("index"))
    
    # Normal password check
    if not user.check_password(password):
        flash("Invalid credentials", "danger")
        return redirect(url_for("auth.login"))
    
    login_user(user)
    return redirect(url_for("index"))


@auth_bp.get("/register")
def register():
    return render_template("auth/register.html")


@auth_bp.post("/register")
def register_post():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        flash("All fields are required", "danger")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first():
        flash("Email already in use", "warning")
        return redirect(url_for("auth.register"))

    user = User(name=name, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash("Account created. Please login.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.get("/set-password")
def set_password():
    # Only allow if session indicates a pending reset
    pending_user_id = session.get("pending_password_user_id")
    if not pending_user_id:
        return redirect(url_for("auth.login"))
    user = User.query.get(pending_user_id)
    if not user:
        session.pop("pending_password_user_id", None)
        return redirect(url_for("auth.login"))
    return render_template("auth/set_password.html", user=user)


@auth_bp.post("/set-password")
def set_password_post():
    pending_user_id = session.get("pending_password_user_id")
    if not pending_user_id:
        return redirect(url_for("auth.login"))
    user = User.query.get_or_404(pending_user_id)
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")
    if not password or not confirm:
        flash("Please enter and confirm your new password.", "danger")
        return redirect(url_for("auth.set_password"))
    if password != confirm:
        flash("Passwords do not match", "danger")
        return redirect(url_for("auth.set_password"))

    user.set_password(password)
    db.session.commit()
    session.pop("pending_password_user_id", None)
    login_user(user)
    flash("Password updated.", "success")
    return redirect(url_for("index"))
