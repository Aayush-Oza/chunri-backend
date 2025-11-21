from flask import Blueprint, request
from models import User, Product, Order, OrderItem
from flask_cors import cross_origin

admin_bp = Blueprint('admin', __name__)


# -----------------------------------------------------------
# ADMIN STATS
# -----------------------------------------------------------
@admin_bp.route('/stats', methods=["GET", "OPTIONS"])
@cross_origin()
def stats():
    if request.method == "OPTIONS":
        return {}, 200

    return {
        "users": User.query.count(),
        "products": Product.query.count(),
        "orders": Order.query.count()
    }


# -----------------------------------------------------------
# ALL CUSTOMERS
# -----------------------------------------------------------
@admin_bp.route('/customers', methods=["GET", "OPTIONS"])
@cross_origin()
def get_customers():
    if request.method == "OPTIONS":
        return {}, 200

    users = User.query.all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "address": u.address
        }
        for u in users
    ]


# -----------------------------------------------------------
# ALL ORDERS (FOR ADMIN)
# -----------------------------------------------------------
@admin_bp.route('/all-orders', methods=["GET", "OPTIONS"])
@cross_origin()
def get_all_orders():
    if request.method == "OPTIONS":
        return {}, 200

    orders = Order.query.order_by(Order.id.desc()).all()
    output = []

    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()

        output.append({
            "order_id": o.id,
            "user_id": o.user_id,
            "total_price": o.total_price,
            "payment_status": o.payment_status,
            "created_at": o.created_at,
            "items": [
                {
                    "product_id": i.product_id,
                    "qty": i.quantity,
                    "price": i.price
                }
                for i in items
            ]
        })

    return output
