from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash

from ..forms import LoginFormData, parse_login_form, validate_login_form

bp = Blueprint("auth", __name__)


def _resolve_next_target(default: str) -> str:
    """Return a safe redirect target."""
    candidate = request.values.get("next")
    if candidate and candidate.startswith("/") and not candidate.startswith("//"):
        return candidate
    return default


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user"):
        return redirect(url_for("leads.list_leads"))

    form_data = LoginFormData()
    errors: list[str] = []
    next_target = _resolve_next_target(url_for("leads.list_leads"))

    if request.method == "POST":
        form_data = parse_login_form(request.form)
        errors = validate_login_form(form_data)

        if not errors:
            admin_username = current_app.config["ADMIN_USERNAME"]
            admin_password_hash = current_app.config["ADMIN_PASSWORD_HASH"]

            if form_data.username == admin_username and check_password_hash(
                admin_password_hash,
                form_data.password,
            ):
                session.clear()
                session["user"] = admin_username
                session["is_admin"] = True
                flash("Welcome back to AI-CRM.", "success")
                return redirect(next_target)

            errors.append("Invalid username or password.")

    return render_template(
        "auth/login.html",
        form=form_data.as_dict(),
        errors=errors,
        next_url=next_target,
        title="Sign In",
    )


@bp.route("/logout")
def logout():
    if session.get("user"):
        session.clear()
        flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
