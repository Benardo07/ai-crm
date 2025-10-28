from dataclasses import dataclass
from typing import Mapping

from ..models import Lead


@dataclass(slots=True)
class LeadFormData:
    """Structured representation of lead form input."""

    name: str = ""
    email: str = ""
    phone: str = ""
    status: str = Lead.STATUS_CHOICES[0]
    notes: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "notes": self.notes,
        }


def parse_lead_form(form: Mapping[str, str | None]) -> LeadFormData:
    """Extracts normalized form data from the request payload."""
    return LeadFormData(
        name=(form.get("name") or "").strip(),
        email=(form.get("email") or "").strip().lower(),
        phone=(form.get("phone") or "").strip(),
        status=(form.get("status") or Lead.STATUS_CHOICES[0]).strip(),
        notes=(form.get("notes") or "").strip(),
    )


def validate_lead_form(data: LeadFormData) -> list[str]:
    """Validates the submitted lead form data."""
    errors: list[str] = []
    if not data.name:
        errors.append("Name is required.")
    if not data.email:
        errors.append("Email is required.")
    if data.status not in Lead.STATUS_CHOICES:
        errors.append("Status must be a valid option.")
    return errors
