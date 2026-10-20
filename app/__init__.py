"""Flask application factory."""

import os

import click
from dotenv import load_dotenv
from flask import Flask
from werkzeug.security import generate_password_hash

from config import Config
from .extensions import db, login_manager


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
    login_manager.init_app(app)

    from .models import User  # noqa: F401 - registers models with SQLAlchemy
    from .routes.auth import auth_bp
    from .routes.main import main_bp

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    register_cli_commands(app)

    register_error_handlers(app)
    return app


def register_cli_commands(app: Flask) -> None:
    """Register safe local administration commands."""

    from .models import User

    @app.cli.command("create-admin")
    @click.option("--username", prompt="Administrator username")
    @click.option(
        "--password",
        prompt="Administrator password",
        hide_input=True,
        confirmation_prompt=True,
    )
    def create_admin(username: str, password: str) -> None:
        """Create the first dashboard administrator account."""

        username = username.strip()
        if not username or not password:
            raise click.ClickException("Username and password are required.")

        if User.query.filter_by(username=username).first():
            raise click.ClickException(f"User '{username}' already exists.")

        user = User(username=username)
        user.password_hash = generate_password_hash(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Administrator '{username}' created successfully.")


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

