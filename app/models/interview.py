from datetime import datetime
from ..extensions import db


class Interview(db.Model):
    __tablename__ = "interviews"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="interviews")
    messages = db.relationship("Message", back_populates="interview", cascade="all, delete-orphan")


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interviews.id"), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # system|user|assistant
    content = db.Column(db.Text, nullable=False)
    audio_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    interview = db.relationship("Interview", back_populates="messages")
