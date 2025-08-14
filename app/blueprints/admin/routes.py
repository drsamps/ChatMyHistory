from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ...extensions import db
from ...models.user import User
from ...models.prompt import Prompt
from ...models.persona import CommStyle, Persona, PersonaStyle
import yaml
import os


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
    personas = Persona.query.order_by(Persona.is_system.desc(), Persona.name.asc()).all()
    comm_styles = CommStyle.query.order_by(CommStyle.sort.asc(), CommStyle.style_name.asc()).all()
    return render_template("admin/dashboard.html", users=users, prompts=prompts, personas=personas, comm_styles=comm_styles)


@admin_bp.post("/styles/seed")
@login_required
def seed_comm_styles():
    # Load from ses_specs/comm_styles.yaml
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # app/blueprints -> app
    project_root = os.path.dirname(root)
    yaml_path = os.path.join(project_root, "ses_specs", "comm_styles.yaml")
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        flash(f"Failed to read comm_styles.yaml: {e}", "danger")
        return redirect(url_for("admin.dashboard"))

    created = 0
    updated = 0
    sort_index = 0
    for key, prompt in data.items():
        sort_index += 10
        # Normalize key: handle YAML null key and whitespace
        key_str = key if isinstance(key, str) else "null"
        key_str = (key_str or "null").strip() or "null"
        # Suggested display name
        def _to_name(k: str) -> str:
            base = k.replace("_", " ").replace("-", " ")
            return base.title()

        style = CommStyle.query.filter_by(key=key_str).first()
        if style:
            style.prompt = str(prompt or "").strip()
            if not style.style_name:
                style.style_name = _to_name(key_str)
            style.sort = style.sort or sort_index
            updated += 1
        else:
            style = CommStyle(
                key=key_str,
                style_name=_to_name(key_str),
                visible=True,
                sort=sort_index,
                prompt=str(prompt or "").strip(),
            )
            db.session.add(style)
            created += 1
    db.session.commit()
    flash(f"Styles synced. Created {created}, updated {updated}.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/personas")
@login_required
def create_persona():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    is_default = request.form.get("is_default") == "on"
    is_system = request.form.get("is_system") == "on" and current_user.is_admin
    style_ids = request.form.getlist("style_ids")

    if not name:
        flash("Persona name is required", "danger")
        return redirect(url_for("admin.dashboard"))

    persona = Persona(name=name, description=description or None, is_default=is_default, is_system=is_system)
    if not is_system:
        persona.user_id = current_user.id
    db.session.add(persona)
    db.session.flush()

    # Clear other defaults for the same scope
    if is_default:
        if is_system:
            Persona.query.filter_by(is_system=True, is_default=True).update({Persona.is_default: False})
        else:
            Persona.query.filter_by(user_id=current_user.id, is_system=False, is_default=True).update({Persona.is_default: False})

    # Attach styles
    for sid in style_ids:
        try:
            s_id = int(sid)
        except Exception:
            continue
        if not CommStyle.query.get(s_id):
            continue
        db.session.add(PersonaStyle(persona_id=persona.id, comm_style_id=s_id))

    db.session.commit()
    flash("Persona saved", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/personas/<int:persona_id>/delete")
@login_required
def delete_persona(persona_id: int):
    p = Persona.query.get_or_404(persona_id)
    if not p.is_system and p.user_id != current_user.id and not current_user.is_admin:
        flash("Not authorized to delete this persona", "danger")
        return redirect(url_for("admin.dashboard"))
    db.session.delete(p)
    db.session.commit()
    flash("Persona deleted", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.post("/personas/<int:persona_id>/default")
@login_required
def set_default_persona(persona_id: int):
    p = Persona.query.get_or_404(persona_id)
    scope_filter = {"is_system": True} if p.is_system else {"user_id": current_user.id, "is_system": False}
    Persona.query.filter_by(**scope_filter, is_default=True).update({Persona.is_default: False})
    p.is_default = True
    db.session.commit()
    flash("Default persona set", "success")
    return redirect(url_for("admin.dashboard"))


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
        # Set password_hash to empty string to indicate no password is set
        # This allows the user to be redirected to set-password on next login
        # Both None and empty string will work with the login logic
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
