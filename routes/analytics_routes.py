from flask import Blueprint
from models import db, OrderItem, Product
from sqlalchemy import func   # 🔥 REQUIRED
from flask_cors import cross_origin


analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.get('/sales-by-color')
@cross_origin()
def sales_by_color():
    results = db.session.query(Product.color, func.sum(OrderItem.quantity)) \
        .join(Product, Product.id == OrderItem.product_id) \
        .group_by(Product.color).all()

    return {color: qty for color, qty in results}

@analytics_bp.get('/sales-by-design')
@cross_origin()
def sales_by_design():
    results = db.session.query(Product.design, func.sum(OrderItem.quantity)) \
        .join(Product, Product.id == OrderItem.product_id) \
        .group_by(Product.design).all()

    return {design: qty for design, qty in results}

@analytics_bp.get('/sales-by-cloth')
@cross_origin()
def sales_by_cloth():
    results = db.session.query(Product.cloth_type, func.sum(OrderItem.quantity)) \
        .join(Product, Product.id == OrderItem.product_id) \
        .group_by(Product.cloth_type).all()

    return {cloth: qty for cloth, qty in results}
