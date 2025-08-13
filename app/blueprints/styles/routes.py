from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ...extensions import db
from ...models.persona import CommStyle, Persona, PersonaStyle


styles_bp = Blueprint("styles", __name__)


@styles_bp.get("/")
@login_required
def styles_home():
	comm_styles = CommStyle.query.order_by(CommStyle.sort.asc(), CommStyle.style_name.asc()).all()
	my_personas = Persona.query.filter_by(user_id=current_user.id).order_by(Persona.name.asc()).all()
	system_personas = Persona.query.filter_by(is_system=True).order_by(Persona.name.asc()).all()

	# Optional edit mode
	edit_id = request.args.get("edit")
	editing_persona = None
	selected_style_ids = set()
	if edit_id:
		try:
			pid = int(edit_id)
		except Exception:
			pid = None
		if pid:
			p = Persona.query.get(pid)
			if p and not p.is_system and p.user_id == current_user.id:
				editing_persona = p
				selected_style_ids = {ps.comm_style_id for ps in p.styles}

	return render_template(
		"styles/index.html",
		comm_styles=comm_styles,
		my_personas=my_personas,
		system_personas=system_personas,
		editing_persona=editing_persona,
		selected_style_ids=selected_style_ids,
	)


@styles_bp.post("/personas")
@login_required
def create_persona():
	name = request.form.get("name", "").strip()
	description = request.form.get("description", "").strip()
	is_default = request.form.get("is_default") == "on"
	style_ids = request.form.getlist("style_ids")
	if not name:
		flash("Persona name is required", "danger")
		return redirect(url_for("styles.styles_home"))
	persona = Persona(name=name, description=description or None, is_default=is_default, is_system=False, user_id=current_user.id)
	db.session.add(persona)
	db.session.flush()
	if is_default:
		Persona.query.filter_by(user_id=current_user.id, is_system=False, is_default=True).update({Persona.is_default: False})
		current_user.default_persona_id = persona.id
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
	return redirect(url_for("styles.styles_home"))


@styles_bp.post("/personas/<int:persona_id>/default")
@login_required
def set_default_persona(persona_id: int):
	p = Persona.query.get_or_404(persona_id)
	if p.user_id and p.user_id != current_user.id:
		flash("Not authorized", "danger")
		return redirect(url_for("styles.styles_home"))
	Persona.query.filter_by(user_id=current_user.id, is_system=False, is_default=True).update({Persona.is_default: False})
	p.is_default = True
	current_user.default_persona_id = p.id
	db.session.commit()
	flash("Default persona set", "success")
	return redirect(url_for("styles.styles_home"))


@styles_bp.post("/personas/<int:persona_id>/edit")
@login_required
def update_persona(persona_id: int):
	p = Persona.query.get_or_404(persona_id)
	# Only allow editing own non-system personas
	if p.is_system or p.user_id != current_user.id:
		flash("Not authorized", "danger")
		return redirect(url_for("styles.styles_home"))

	name = request.form.get("name", "").strip()
	description = request.form.get("description", "").strip()
	is_default = request.form.get("is_default") == "on"
	style_ids = request.form.getlist("style_ids")

	if not name:
		flash("Persona name is required", "danger")
		return redirect(url_for("styles.styles_home", edit=persona_id))

	# Update core fields
	p.name = name
	p.description = description or None
	p.is_default = is_default

	# Handle default logic for this user
	if is_default:
		Persona.query.filter_by(user_id=current_user.id, is_system=False, is_default=True).update({Persona.is_default: False})
		p.is_default = True
		current_user.default_persona_id = p.id
	else:
		# If turning off default on this persona, clear user's default reference if pointing here
		if current_user.default_persona_id == p.id:
			current_user.default_persona_id = None

	# Replace styles
	# Clear existing
	for ps in list(p.styles):
		db.session.delete(ps)
	# Add selected
	for sid in style_ids:
		try:
			s_id = int(sid)
		except Exception:
			continue
		if not CommStyle.query.get(s_id):
			continue
		db.session.add(PersonaStyle(persona_id=p.id, comm_style_id=s_id))

	db.session.commit()
	flash("Persona updated", "success")
	return redirect(url_for("styles.styles_home"))


