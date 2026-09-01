import json
import random
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .extensions import db


def gen_ref_id():
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return "NRF-" + "".join(random.choice(chars) for _ in range(5))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship(
        "Application", backref="owner", lazy=True, foreign_keys="Application.owner_id"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def initial(self):
        return self.full_name[:1].upper() if self.full_name else "?"


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ref_id = db.Column(db.String(12), unique=True, nullable=False, default=gen_ref_id)
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    id_type = db.Column(db.String(20), nullable=False)
    id_number = db.Column(db.String(60), nullable=False)
    address = db.Column(db.Text, nullable=False)
    needs_json = db.Column(db.Text, nullable=False, default="[]")
    total = db.Column(db.Float, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="Under review")
    account_number = db.Column(db.String(60), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    @property
    def needs(self):
        return json.loads(self.needs_json)

    @needs.setter
    def needs(self, value):
        self.needs_json = json.dumps(value)

    @property
    def needs_summary(self):
        return ", ".join(n["item"] for n in self.needs)

    def mask_id(self):
        s = self.id_number
        if len(s) <= 4:
            return "\u2022\u2022\u2022\u2022"
        return "\u2022" * max(len(s) - 4, 0) + s[-4:]

    @property
    def region(self):
        parts = self.address.split(",")
        return parts[-1].strip() if parts and parts[-1].strip() else self.address

    @property
    def first_name(self):
        parts = self.full_name.split()
        return parts[0] if parts else self.full_name

    @property
    def last_initial(self):
        parts = self.full_name.split()
        return parts[-1][:1] if len(parts) > 1 else ""
