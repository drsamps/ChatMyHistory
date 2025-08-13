from datetime import datetime
from ..extensions import db


class Media(db.Model):
    __tablename__ = "media"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interviews.id"), nullable=True, index=True)
    kind = db.Column(db.String(20), nullable=False)  # photo|audio|video|document
    file_path = db.Column(db.String(512), nullable=False)
    caption = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
