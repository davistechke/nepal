from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user

from ..extensions import db
from ..models import Application

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)

    return wrapper


@admin_bp.route("", strict_slashes=False)
@admin_required
def admin_panel():
    applications = Application.query.order_by(Application.timestamp.desc()).all()
    total_requested = sum(a.total for a in applications)
    return render_template(
        "admin.html", applications=applications, total_requested=total_requested
    )


@admin_bp.route("/status/<ref_id>", methods=["POST"])
@admin_required
def admin_update_status(ref_id):
    application = Application.query.filter_by(ref_id=ref_id).first_or_404()
    new_status = request.form.get("status")
    if new_status in ("Under review", "Approved", "Declined"):
        application.status = new_status
        db.session.commit()
        flash(f"{ref_id} marked {new_status}.", "admin_success")
    return redirect(url_for("admin.admin_panel"))


@admin_bp.route("/recent")
@admin_required
def recent():
    applications = Application.query.order_by(Application.timestamp.desc()).limit(15).all()
    return render_template("recent.html", recent=applications)
