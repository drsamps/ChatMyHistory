from datetime import datetime
from ..extensions import db


class Summary(db.Model):
    __tablename__ = "summaries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    interview_id = db.Column(db.Integer, db.ForeignKey("interviews.id"), nullable=False, index=True)
    # kind allows future expansion (e.g., 'session', 'life_story', 'themes', etc.)
    kind = db.Column(db.String(50), nullable=False, default="session")
    format = db.Column(db.String(20), nullable=False, default="html")  # html|markdown|text
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("interview_id", "kind", name="uq_summary_interview_kind"),
    )


