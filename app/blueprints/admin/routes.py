from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ...extensions import db
from ...models.user import User
from ...models.prompt import Prompt


admin_bp = Blueprint("admin", __name__)


def admin_required():
    return current_user.is_authenticated and current_user.is_admin


@admin_bp.before_request
def check_admin():
    if not admin_required():
        return redirect(url_for("auth.login"))


@admin_bp.get("/")
@login_required
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    prompts = Prompt.query.order_by(Prompt.updated_at.desc()).all()
    return render_template("admin/dashboard.html", users=users, prompts=prompts)


@admin_bp.post("/users")
@login_required
def create_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    is_admin = request.form.get("is_admin") == "on"

    if not name or not email or not password:
        flash("All fields are required", "danger")
        return redirect(url_for("admin.dashboard"))

    if User.query.filter_by(email=email).first():
        flash("Email already exists", "warning")
        return redirect(url_for("admin.dashboard"))

    user = User(name=name, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash("User created", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/users/<int:user_id>/delete")
@login_required
def delete_user(user_id: int):
    if user_id == current_user.id:
        flash("You cannot delete your own account", "warning")
        return redirect(url_for("admin.dashboard"))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.get("/users/<int:user_id>/edit")
@login_required
def edit_user(user_id: int):
    user = User.query.get_or_404(user_id)
    return render_template("admin/user_edit.html", user=user)


@admin_bp.post("/users/<int:user_id>/edit")
@login_required
def edit_user_post(user_id: int):
    user = User.query.get_or_404(user_id)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    is_admin = request.form.get("is_admin") == "on"
    reset_password = request.form.get("reset_password") == "on"

    if not name or not email:
        flash("Name and email are required", "danger")
        return redirect(url_for("admin.edit_user", user_id=user.id))

    # Prevent email collision
    existing = User.query.filter(User.email == email, User.id != user.id).first()
    if existing:
        flash("Another account already uses that email", "warning")
        return redirect(url_for("admin.edit_user", user_id=user.id))

    user.name = name
    user.email = email
    user.is_admin = is_admin

    if reset_password:
        # Use empty string to support databases that may still have NOT NULL constraint
        user.password_hash = ""

    db.session.commit()
    flash("User updated", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/prompts")
@login_required
def create_prompt():
    name = request.form.get("name", "").strip()
    content = request.form.get("content", "").strip()
    if not name or not content:
        flash("Name and content required", "danger")
        return redirect(url_for("admin.dashboard"))
    prompt = Prompt(name=name, content=content)
    db.session.add(prompt)
    db.session.commit()
    flash("Prompt saved", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/prompts/<int:prompt_id>/delete")
@login_required
def delete_prompt(prompt_id: int):
    prompt = Prompt.query.get_or_404(prompt_id)
    db.session.delete(prompt)
    db.session.commit()
    flash("Prompt deleted", "success")
    return redirect(url_for("admin.dashboard"))
