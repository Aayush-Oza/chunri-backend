from flask import Blueprint
from models import User, Product, Order

admin_bp = Blueprint('admin', __name__)

@admin_bp.get('/stats')
def stats():
    return {
        "users": User.query.count(),
        "products": Product.query.count(),
        "orders": Order.query.count()
    }
