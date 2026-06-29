from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Vehicle
from app.forms import VehicleForm

vehicles_bp = Blueprint("vehicles", __name__, url_prefix="/vehicles")


@vehicles_bp.route("/")
@login_required
def index():
    vehicles = Vehicle.query.order_by(Vehicle.created_at.desc()).all()
    return render_template("vehicles/index.html", vehicles=vehicles)


@vehicles_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for("vehicles.index"))
    form = VehicleForm()
    if form.validate_on_submit():
        vehicle = Vehicle(
            name=form.name.data,
            model=form.model.data,
            year=form.year.data,
            category=form.category.data,
            price=form.price.data,
            stock=form.stock.data,
            description=form.description.data,
        )
        db.session.add(vehicle)
        db.session.commit()
        flash("Vehicle added successfully.", "success")
        return redirect(url_for("vehicles.index"))
    return render_template("vehicles/form.html", form=form, title="Add vehicle")


@vehicles_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit(id):
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for("vehicles.index"))
    vehicle = Vehicle.query.get_or_404(id)
    form = VehicleForm(obj=vehicle)
    if form.validate_on_submit():
        form.populate_obj(vehicle)
        db.session.commit()
        flash("Vehicle updated.", "success")
        return redirect(url_for("vehicles.index"))
    return render_template("vehicles/form.html", form=form, title="Edit vehicle")


@vehicles_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete(id):
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for("vehicles.index"))
    vehicle = Vehicle.query.get_or_404(id)
    db.session.delete(vehicle)
    db.session.commit()
    flash("Vehicle deleted.", "info")
    return redirect(url_for("vehicles.index"))
