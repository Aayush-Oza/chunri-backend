from flask import Blueprint
from models import User, Product, Order, OrderItem
from flask_cors import cross_origin

admin_bp = Blueprint('admin', __name__)

@admin_bp.get('/stats')
@cross_origin()
def stats():
    return {
        "users": User.query.count(),
        "products": Product.query.count(),
        "orders": Order.query.count()
    }


# -----------------------------------------------------------
# 📌 NEW: ALL CUSTOMERS LIST (for customers.html)
# -----------------------------------------------------------
@admin_bp.get('/customers')
@cross_origin()
def get_customers():
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
# 📌 NEW: ALL ORDERS LIST (for orders.html)
# -----------------------------------------------------------
@admin_bp.get('/all-orders')
@cross_origin()
def get_all_orders():
    orders = Order.query.all()
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
