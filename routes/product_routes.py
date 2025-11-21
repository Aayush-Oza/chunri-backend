from flask import Blueprint, request
from models import db, Product
from flask_cors import CORS, cross_origin

product_bp = Blueprint('product', __name__)
CORS(product_bp)     # important


# -----------------------------------------------------------
# GET PRODUCTS (with filters)
# -----------------------------------------------------------
@product_bp.route('/products', methods=["GET", "OPTIONS"])
@cross_origin()
def get_products():
    if request.method == "OPTIONS":
        return {}, 200

    cloth = request.args.get("cloth_type")
    size = request.args.get("size")
    color = request.args.get("color")
    design = request.args.get("design")
    search = request.args.get("search")

    query = Product.query.filter_by(is_active=True)

    if cloth:
        query = query.filter_by(cloth_type=cloth)
    if size:
        query = query.filter_by(size=size)
    if color:
        query = query.filter_by(color=color)
    if design:
        query = query.filter_by(design=design)
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))

    products = query.all()

    return [{
        "id": p.id,
        "product_no": p.product_no,
        "name": p.name,
        "price": p.price,
        "image_url": p.image_url,
        "stock": p.stock,
        "cloth_type": p.cloth_type,
        "design": p.design,
        "size": p.size,
        "color": p.color
    } for p in products]


# -----------------------------------------------------------
# ADD PRODUCT
# -----------------------------------------------------------
@product_bp.route('/product', methods=["POST", "OPTIONS"])
@cross_origin()
def add_product():
    if request.method == "OPTIONS":
        return {}, 200

    data = request.json

    p = Product(
        product_no=data.get("product_no"),
        name=data.get("name"),
        description=data.get("description"),
        price=data.get("price"),
        stock=data.get("stock"),
        cloth_type=data.get("cloth_type"),
        design=data.get("design"),
        size=data.get("size"),
        color=data.get("color"),
        image_url=data.get("image_url")
    )

    db.session.add(p)
    db.session.commit()
    return {"message": "Product added successfully!"}


# -----------------------------------------------------------
# DELETE PRODUCT (SOFT DELETE)
# -----------------------------------------------------------
@product_bp.delete("/product/<int:product_id>")
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return {"error": "Product not found"}, 404

        product.is_active = False
        db.session.commit()

        return {"message": "Product deleted (soft delete)"}

    except Exception as e:
        db.session.rollback()
        print("DELETE ERROR:", e)
        return {"error": str(e)}, 500


# -----------------------------------------------------------
# UPDATE PRODUCT
# -----------------------------------------------------------
@product_bp.route('/product/<int:id>', methods=["PUT", "OPTIONS"])
@cross_origin()
def update_product(id):
    if request.method == "OPTIONS":
        return {}, 200

    data = request.json
    product = Product.query.get(id)

    if not product:
        return {"error": "Product not found"}, 404

    for key in [
        "product_no", "name", "price", "stock", "cloth_type",
        "design", "size", "color", "description", "image_url"
    ]:
        if key in data:
            setattr(product, key, data[key])

    db.session.commit()
    return {"message": "Product updated successfully!"}

