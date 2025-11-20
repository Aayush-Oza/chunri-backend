from flask import Blueprint, request, send_file
from models import db, Order, OrderItem, Product
from fpdf import FPDF
from utils.email_helper import send_email
from flask_cors import cross_origin

order_bp = Blueprint("order", __name__)

# CHECKOUT
@order_bp.route("/checkout", methods=["POST"])
@cross_origin()
def checkout():
    try:
        data = request.json or {}

        user_id = data.get("user_id")
        name = data.get("name", "")
        email = data.get("email", "")
        phone = data.get("phone", "")
        address = data.get("address", "")
        payment = data.get("payment", "")
        items = data.get("items", [])

        if not user_id:
            return {"error": "user_id is required"}, 400

        if not items:
            return {"error": "No items found in order"}, 400

        order = Order(
            user_id=user_id,
            total_price=0,
            payment_status="pending",
            customer_name=name,
            customer_email=email,
            customer_phone=phone,
            customer_address=address,
            payment_method=payment
        )
        db.session.add(order)
        db.session.commit()

        total_amount = 0

        for it in items:
            product = Product.query.get(it["product_id"])
            if not product:
                continue

            qty = it.get("qty", 1)
            subtotal = qty * product.price
            total_amount += subtotal

            new_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                price=product.price
            )
            db.session.add(new_item)

        order.total_price = total_amount
        db.session.commit()

        return {
            "message": "Order placed successfully",
            "order_id": order.id,
            "total_amount": total_amount
        }

    except Exception as e:
        print("CHECKOUT ERROR:", e)
        return {"error": "Server crashed"}, 500


# PRE-FLIGHT
@order_bp.route("/checkout", methods=["OPTIONS"])
@cross_origin()
def checkout_options():
    return {}, 200
