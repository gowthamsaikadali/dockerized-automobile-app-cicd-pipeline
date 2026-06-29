from flask import Blueprint, render_template
from flask_login import login_required
from app.models import Vehicle, Order, User

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    total_vehicles = Vehicle.query.count()
    total_orders = Order.query.count()
    total_users = User.query.count()
    pending_orders = Order.query.filter_by(status="pending").count()
    recent_orders = (
        Order.query.order_by(Order.created_at.desc()).limit(5).all()
    )
    return render_template(
        "dashboard/index.html",
        total_vehicles=total_vehicles,
        total_orders=total_orders,
        total_users=total_users,
        pending_orders=pending_orders,
        recent_orders=recent_orders,
    )
