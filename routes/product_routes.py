from flask import Blueprint, request
from models import db, Product
from flask_cors import cross_origin

product_bp = Blueprint('product', __name__)

@product_bp.get('/products')
@cross_origin()
def get_products():
    cloth = request.args.get("cloth_type")
    size = request.args.get("size")
    color = request.args.get("color")
    design = request.args.get("design")
    search = request.args.get("search")   # <-- ADD THIS

    query = Product.query

    if cloth:
        query = query.filter_by(cloth_type=cloth)
    if size:
        query = query.filter_by(size=size)
    if color:
        query = query.filter_by(color=color)
    if design:
        query = query.filter_by(design=design)
    if search:  # <--- ADD THIS FILTER
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.all()

    return [{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "image_url": p.image_url,
        "stock": p.stock,
        "cloth_type": p.cloth_type,
        "design": p.design,
        "size": p.size,
        "color": p.color
    } for p in products]


# ADD PRODUCT
@product_bp.post('/product')
def add_product():
    data = request.json
    p = Product(**data)
    db.session.add(p)
    db.session.commit()
    return {"message": "Product added"}

# DELETE PRODUCT
@product_bp.delete('/product/<int:id>')
def delete_product(id):
    product = Product.query.get(id)
    if not product:
        return {"error": "Product not found"}, 404

    db.session.delete(product)
    db.session.commit()
    return {"message": "Product deleted"}

# UPDATE PRODUCT
@product_bp.put('/product/<int:id>')
def update_product(id):
    data = request.json
    product = Product.query.get(id)

    if not product:
        return {"error": "Product not found"}, 404

    for key in ["name", "price", "stock", "cloth_type", "design", "size", "color", "description", "image_url"]:
        if key in data:
            setattr(product, key, data[key])

    db.session.commit()
    return {"message": "Product updated"}
