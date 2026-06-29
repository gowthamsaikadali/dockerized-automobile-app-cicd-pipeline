from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Order, Vehicle
from app.forms import OrderForm, UpdateOrderStatusForm

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/")
@login_required
def index():
    if current_user.is_admin:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    else:
        orders = (
            Order.query
            .filter_by(user_id=current_user.id)
            .order_by(Order.created_at.desc())
            .all()
        )
    return render_template("orders/index.html", orders=orders)


@orders_bp.route("/place/<int:vehicle_id>", methods=["GET", "POST"])
@login_required
def place(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    form = OrderForm()
    if form.validate_on_submit():
        if form.quantity.data > vehicle.stock:
            flash(f"Only {vehicle.stock} units available.", "danger")
            return redirect(url_for("orders.place", vehicle_id=vehicle_id))
        order = Order(
            user_id=current_user.id,
            vehicle_id=vehicle.id,
            quantity=form.quantity.data,
            total_price=vehicle.price * form.quantity.data,
        )
        vehicle.stock -= form.quantity.data
        db.session.add(order)
        db.session.commit()
        flash("Order placed successfully!", "success")
        return redirect(url_for("orders.index"))
    return render_template("orders/place.html", form=form, vehicle=vehicle)


@orders_bp.route("/update/<int:order_id>", methods=["GET", "POST"])
@login_required
def update_status(order_id):
    if not current_user.is_admin:
        flash("Admin access required.", "danger")
        return redirect(url_for("orders.index"))
    order = Order.query.get_or_404(order_id)
    form = UpdateOrderStatusForm(obj=order)
    if form.validate_on_submit():
        order.status = form.status.data
        db.session.commit()
        flash("Order status updated.", "success")
        return redirect(url_for("orders.index"))
    return render_template("orders/update.html", form=form, order=order)
