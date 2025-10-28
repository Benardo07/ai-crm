from dataclasses import dataclass
from typing import Mapping


@dataclass(slots=True)
class LoginFormData:
    """Structured login form payload."""

    username: str = ""
    password: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"username": self.username, "password": self.password}


def parse_login_form(form: Mapping[str, str | None]) -> LoginFormData:
    """Normalize login form submission."""
    return LoginFormData(
        username=(form.get("username") or "").strip(),
        password=form.get("password") or "",
    )


def validate_login_form(data: LoginFormData) -> list[str]:
    """Validate login form fields."""
    errors: list[str] = []
    if not data.username:
        errors.append("Username is required.")
    if not data.password:
        errors.append("Password is required.")
    return errors
