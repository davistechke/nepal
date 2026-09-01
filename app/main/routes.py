import re
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user

from ..extensions import db
from ..models import Application, gen_ref_id

main_bp = Blueprint("main", __name__)

PHONE_RE = re.compile(r"^\+?977(\d{9,10})$")


def is_valid_nepal_phone(raw: str) -> bool:
    cleaned = re.sub(r"[\s-]", "", raw or "")
    match = PHONE_RE.match(cleaned)
    if not match:
        return False
    return bool(re.match(r"^\d{9,10}$", match.group(1)))


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/account")
@login_required
def account():
    my_applications = (
        Application.query.filter_by(owner_id=current_user.id)
        .order_by(Application.timestamp.desc())
        .all()
    )
    return render_template("account.html", my_applications=my_applications)


@main_bp.route("/apply", methods=["GET", "POST"])
@login_required
def apply():
    if request.method == "GET":
        return render_template("apply.html")

    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    id_type = request.form.get("id_type", "National ID")
    id_number = request.form.get("id_number", "").strip()
    address = request.form.get("address", "").strip()
    need_items = request.form.getlist("need_item[]")
    need_amounts = request.form.getlist("need_amount[]")

    needs = []
    for item, amount in zip(need_items, need_amounts):
        item = item.strip()
        try:
            amount = float(amount)
        except (TypeError, ValueError):
            amount = 0
        if item and amount > 0:
            needs.append({"item": item, "amount": amount})

    errors = []
    if not full_name:
        errors.append("Enter your full name.")
    if not phone:
        errors.append("Enter a phone number we can reach you on.")
    elif not is_valid_nepal_phone(phone):
        errors.append("Enter a valid Nepal number, including the +977 country code.")
    if not id_number:
        errors.append("Enter your ID or passport number.")
    if not address:
        errors.append("Enter your current address.")
    if not needs:
        errors.append("Add at least one affected item with an amount.")

    if errors:
        for e in errors:
            flash(e, "apply_error")
        return redirect(url_for("main.apply"))

    ref_id = gen_ref_id()
    while Application.query.filter_by(ref_id=ref_id).first():
        ref_id = gen_ref_id()

    application = Application(
        ref_id=ref_id,
        full_name=full_name,
        phone=phone,
        id_type=id_type,
        id_number=id_number,
        address=address,
        total=sum(n["amount"] for n in needs),
        status="Under review",
        timestamp=datetime.utcnow(),
        owner_id=current_user.id,
    )
    application.needs = needs
    db.session.add(application)
    db.session.commit()

    flash(f"Submitted. Your reference number is {ref_id}.", "apply_success")
    return redirect(url_for("main.apply"))


@main_bp.route("/account/payout/<ref_id>", methods=["POST"])
@login_required
def submit_payout(ref_id):
    application = Application.query.filter_by(
        ref_id=ref_id, owner_id=current_user.id
    ).first_or_404()

    if application.status != "Approved":
        abort(403)

    account_number = request.form.get("account_number", "").strip()
    if not re.match(r"^\d{5,20}$", account_number):
        flash("Enter a valid account number (digits only, 5-20 characters).", "payout_error")
        return redirect(url_for("main.account"))

    application.account_number = account_number
    db.session.commit()
    flash(f"Account number saved for {ref_id}. Funds will be sent there.", "payout_success")
    return redirect(url_for("main.account"))
