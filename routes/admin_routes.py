from flask import Blueprint
from models import User, Product, Order
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
