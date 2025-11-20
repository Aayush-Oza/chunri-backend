from flask import Blueprint, request
from models import db, Cart, Product
from flask_cors import cross_origin


cart_bp = Blueprint("cart", __name__)

# -------------------------------------------------
# SAFE GET CART (AUTO-REMOVES INVALID PRODUCT ROWS)
# -------------------------------------------------
@cart_bp.get("/cart/<int:user_id>")
@cross_origin()
def get_cart(user_id):
    items = Cart.query.filter_by(user_id=user_id).all()
    result = []
    cleaned = False

    for item in items:
        product = Product.query.get(item.product_id)

        if not product:
            # INVALID cart row → delete it permanently
            db.session.delete(item)
            cleaned = True
            continue

        result.append({
            "cart_id": item.id,
            "product_id": product.id,
            "name": product.name,
            "price": product.price,
            "image_url": product.image_url,
            "qty": item.qty,
            "subtotal": product.price * item.qty
        })

    if cleaned:
        db.session.commit()

    return result


# -------------------------------------------------
# ADD TO CART (SAFE)
# -------------------------------------------------
@cart_bp.post("/cart/add")
@cross_origin()
def add_to_cart():
    data = request.json
    user_id = data.get("user_id")
    product_id = data.get("product_id")
    qty = data.get("qty", 1)

    # CHECK product exists
    product = Product.query.get(product_id)
    if not product:
        return {"error": "Product does not exist"}, 400

    existing = Cart.query.filter_by(user_id=user_id, product_id=product_id).first()

    if existing:
        existing.qty += qty
    else:
        new_item = Cart(user_id=user_id, product_id=product_id, qty=qty)
        db.session.add(new_item)

    db.session.commit()
    return {"message": "Added to cart"}


# -------------------------------------------------
# UPDATE QTY (SAFE)
# -------------------------------------------------
@cart_bp.put("/cart/update")
@cross_origin()
def update_cart():
    data = request.json
    cart_id = data["cart_id"]
    qty = data["qty"]

    item = Cart.query.get(cart_id)
    if not item:
        return {"error": "Cart item not found"}, 404

    # Prevent invalid values
    if qty < 1:
        qty = 1

    item.qty = qty
    db.session.commit()
    return {"message": "Quantity updated"}


# -------------------------------------------------
# DELETE ITEM (SAFE)
# -------------------------------------------------
@cart_bp.delete("/cart/delete/<int:cart_id>")
@cross_origin()
def delete_cart(cart_id):
    item = Cart.query.get(cart_id)
    if not item:
        return {"error": "Cart item not found"}, 404

    db.session.delete(item)
    db.session.commit()
    return {"message": "Item removed"}


# -------------------------------------------------
# CLEAR CART (SAFE)
# -------------------------------------------------
@cart_bp.delete("/cart/clear/<int:user_id>")
@cross_origin()
def clear_cart(user_id):
    Cart.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return {"message": "Cart cleared"}
