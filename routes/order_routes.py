from flask import Blueprint, request, send_file
from models import db, Order, OrderItem, Product
from fpdf import FPDF
from utils.email_helper import send_email
from flask_cors import CORS, cross_origin

order_bp = Blueprint("order", __name__)
CORS(order_bp)   # IMPORTANT


# ---------------------- CHECKOUT -----------------------
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


# ---------------------- PRE-FLIGHT -----------------------
@order_bp.route("/checkout", methods=["OPTIONS"])
@cross_origin()
def checkout_options():
    return {}, 200


# ---------------------- GET ORDERS -----------------------
@order_bp.get("/orders/<int:user_id>")
@cross_origin()
def get_orders(user_id):
    orders = Order.query.filter_by(user_id=user_id).all()
    output = []

    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()

        output.append({
            "order_id": o.id,
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


# ---------------------- INVOICE DOWNLOAD -----------------------
@order_bp.get("/invoice/<int:order_id>")
@cross_origin()
def invoice(order_id):
    order = Order.query.get(order_id)
    items = OrderItem.query.filter_by(order_id=order_id).all()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 14)

    pdf.cell(200, 10, "Chunri Store Invoice", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Arial", 12)
    pdf.cell(200, 10, f"Order ID: {order.id}", ln=True)
    pdf.cell(200, 10, f"Total: ₹{order.total_price}", ln=True)
    pdf.ln(5)

    pdf.cell(80, 10, "Item", 1)
    pdf.cell(30, 10, "Qty", 1)
    pdf.cell(30, 10, "Price", 1)
    pdf.cell(50, 10, "Subtotal", 1, ln=True)

    for item in items:
        product = Product.query.get(item.product_id)
        name = product.name if product else "Unknown"
        subtotal = item.quantity * item.price

        pdf.cell(80, 10, name, 1)
        pdf.cell(30, 10, str(item.quantity), 1)
        pdf.cell(30, 10, str(item.price), 1)
        pdf.cell(50, 10, str(subtotal), 1, ln=True)

    filename = f"invoice_{order_id}.pdf"
    pdf.output(filename)
    return send_file(filename, as_attachment=True)
