import logging
import os

from flask import Flask
from werkzeug.security import generate_password_hash

from .extensions import db


def create_app() -> Flask:
    """Application factory for the CRM app."""
    app = Flask(__name__)

    app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///crm.db",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    configure_settings(app)
    configure_logging(app)
    register_extensions(app)
    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app


def configure_settings(app: Flask) -> None:
    """Configure application defaults and secrets."""
    secret_key = os.environ.get("SECRET_KEY") or "change-me-in-production"
    app.config.setdefault("SECRET_KEY", secret_key)

    admin_username = os.environ.get("ADMIN_USERNAME") or "admin"
    app.config.setdefault("ADMIN_USERNAME", admin_username)

    password_hash = os.environ.get("ADMIN_PASSWORD_HASH")
    if not password_hash:
        admin_password = os.environ.get("ADMIN_PASSWORD") or "AdminPass123!"
        password_hash = generate_password_hash(admin_password)
    app.config.setdefault("ADMIN_PASSWORD_HASH", password_hash)


def configure_logging(app: Flask) -> None:
    """Configure application logging."""
    logger = logging.getLogger("app.services.sentiment")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(levelname)s] %(name)s: %(message)s"),
        )
        logger.addHandler(handler)

    logger.setLevel(logging.INFO)
    logger.propagate = False


def register_extensions(app: Flask) -> None:
    """Register extension instances with the Flask app."""
    db.init_app(app)


def register_blueprints(app: Flask) -> None:
    """Register application blueprints."""
    from .views import auth_bp, leads_bp  # noqa: WPS433

    app.register_blueprint(auth_bp)
    app.register_blueprint(leads_bp)
