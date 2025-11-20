from flask import Blueprint
from models import db, OrderItem, Product

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.get('/sales-by-color')
def sales_by_color():
    results = db.session.query(Product.color, db.func.sum(OrderItem.quantity)) \
        .join(Product, Product.id == OrderItem.product_id) \
        .group_by(Product.color).all()

    return {color: qty for color, qty in results}
@analytics_bp.get('/sales-by-design')
def sales_by_design():
    results = db.session.query(Product.design, db.func.sum(OrderItem.quantity)) \
        .join(Product, Product.id == OrderItem.product_id) \
        .group_by(Product.design).all()
    return {design: qty for design, qty in results}


@analytics_bp.get('/sales-by-cloth')
def sales_by_cloth():
    results = db.session.query(Product.cloth_type, db.func.sum(OrderItem.quantity)) \
        .join(Product, Product.id == OrderItem.product_id) \
        .group_by(Product.cloth_type).all()
    return {cloth: qty for cloth, qty in results}

