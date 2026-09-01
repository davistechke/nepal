"""Shared extension instances, created here (not bound to an app yet) so
blueprint modules can import them without circular imports."""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()
