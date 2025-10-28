from datetime import datetime

from ..extensions import db


class Lead(db.Model):
    """Represents a CRM lead."""

    __tablename__ = "leads"

    STATUS_CHOICES = ["New", "Contacted", "In Progress", "Converted", "Lost"]

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(50))
    status = db.Column(db.String(50), nullable=False, default="New")
    notes = db.Column(db.Text)
    sentiment = db.Column(db.String(50))
    sentiment_score = db.Column(db.Float)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def sentiment_display(self) -> str:
        """Returns human-friendly sentiment text."""
        return (self.sentiment or "Unknown").title()
