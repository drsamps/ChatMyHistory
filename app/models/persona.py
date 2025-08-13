from datetime import datetime
from ..extensions import db


class CommStyle(db.Model):
	__tablename__ = "comm_styles"

	id = db.Column(db.Integer, primary_key=True)
	key = db.Column(db.String(64), unique=True, nullable=False, index=True)
	style_name = db.Column(db.String(128), nullable=False)
	visible = db.Column(db.Boolean, default=True, nullable=False)
	sort = db.Column(db.Integer, default=0, nullable=False)
	prompt = db.Column(db.Text, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	persona_styles = db.relationship("PersonaStyle", back_populates="comm_style", cascade="all, delete-orphan")


class Persona(db.Model):
	__tablename__ = "personas"

	id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
	name = db.Column(db.String(128), nullable=False)
	description = db.Column(db.String(512), nullable=True)
	is_default = db.Column(db.Boolean, default=False, nullable=False)
	is_system = db.Column(db.Boolean, default=False, nullable=False)
	created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
	updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	styles = db.relationship("PersonaStyle", back_populates="persona", cascade="all, delete-orphan")


class PersonaStyle(db.Model):
	__tablename__ = "persona_styles"

	id = db.Column(db.Integer, primary_key=True)
	persona_id = db.Column(db.Integer, db.ForeignKey("personas.id"), nullable=False, index=True)
	comm_style_id = db.Column(db.Integer, db.ForeignKey("comm_styles.id"), nullable=False, index=True)

	persona = db.relationship("Persona", back_populates="styles")
	comm_style = db.relationship("CommStyle", back_populates="persona_styles")


