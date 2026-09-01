import os

import click
from dotenv import load_dotenv
from flask import Flask

from .extensions import db, login_manager

# Project root is one level above this app/ package.
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # DATABASE_URL lets you point at Postgres/MySQL when hosted (Render sets
    # this automatically if you attach a managed database). Falls back to a
    # local SQLite file for plain local runs.
    db_url = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "relief.db")
    )
    if db_url.startswith("postgres://"):  # normalize Render/Heroku-style URLs
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .auth.routes import auth_bp
    from .main.routes import main_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)

    _register_cli(app)

    # Create the database's tables and seed the admin account right when the
    # app starts, so this works the same locally and on a host like Render
    # with no separate manual setup step required.
    with app.app_context():
        db.create_all()
        _seed_admin_from_env()

    return app


def _seed_admin_from_env():
    """Create/promote an admin account from env vars, if provided.

    Set these before running the app (in a .env file locally, or as
    environment variables in your host's dashboard when deployed):
      ADMIN_USERNAME=youradmin
      ADMIN_PASSWORD=a-strong-password
      ADMIN_FULL_NAME="Your Name"   (optional)
    """
    from .models import User

    username = os.environ.get("ADMIN_USERNAME", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    full_name = os.environ.get("ADMIN_FULL_NAME", "Administrator")

    if not username or not password:
        print(
            " * No ADMIN_USERNAME/ADMIN_PASSWORD found in environment or .env "
            "- no admin account seeded."
        )
        return

    user = User.query.filter_by(username=username).first()
    if user:
        if not user.is_admin:
            user.is_admin = True
        user.set_password(password)
    else:
        user = User(username=username, full_name=full_name, is_admin=True)
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    print(f" * Admin account ready: username='{username}' (log in with this at /login)")


def _register_cli(app):
    from .extensions import db
    from .models import User

    @app.cli.command("create-admin")
    @click.argument("username")
    @click.argument("full_name")
    @click.argument("password")
    def create_admin(username, full_name, password):
        """Create an admin account: flask create-admin <username> "<full name>" <password>"""
        username = username.strip().lower()
        existing = User.query.filter_by(username=username).first()
        if existing:
            if existing.is_admin:
                print(f"'{username}' is already an admin.")
            else:
                existing.is_admin = True
                db.session.commit()
                print(f"'{username}' promoted to admin.")
            return
        user = User(username=username, full_name=full_name, is_admin=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Admin account '{username}' created.")


# A ready-to-serve instance, built eagerly at import time, so both of these
# work no matter which one your host is configured to run:
#   gunicorn app:app     (imports this package, uses this variable)
#   gunicorn wsgi:app     (wsgi.py imports this same variable)
app = create_app()
