"""Flask application factory."""

import os

from dotenv import load_dotenv
from flask import Flask

from config import Config
from .extensions import db


def create_app(test_config: dict | None = None) -> Flask:
    """Create and configure the Flask application."""

    load_dotenv()

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"

    os.makedirs(app.instance_path, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = Config.database_uri(app.instance_path)

    if test_config:
        app.config.update(test_config)

    db.init_app(app)

    from .models import User  # noqa: F401 - registers models with SQLAlchemy
    from .routes.main import main_bp

    app.register_blueprint(main_bp)

    with app.app_context():
        db.create_all()

    register_error_handlers(app)
    return app


def register_error_handlers(app: Flask) -> None:
    """Register user-friendly error pages."""

    from flask import render_template

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template("errors/500.html", error=error), 500

