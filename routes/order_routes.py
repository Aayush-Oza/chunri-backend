from flask import Blueprint, request, send_file
from models import db, Order, OrderItem, Product
from fpdf import FPDF
from utils.email_helper import send_email
from flask_cors import CORS, cross_origin
import io


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


@order_bp.get("/invoice/<int:order_id>")
@cross_origin()
def download_invoice(order_id):
    try:
        order = Order.query.get(order_id)
        if not order:
            return {"error": "Order not found"}, 404

        items = OrderItem.query.filter_by(order_id=order_id).all()

        pdf = FPDF()
        pdf.add_page()

        # ---------- HEADER ----------
        pdf.set_font("Arial", "B", 18)
        pdf.set_text_color(214, 40, 40)
        pdf.cell(190, 10, "CHUNRI STORE - INVOICE", ln=True, align="C")
        pdf.ln(5)

        # ---------- META ----------
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(100, 8, f"Invoice No: CHN-{order.id:05}", ln=True)
        pdf.cell(100, 8, f"Date: {order.created_at.strftime('%d-%m-%Y')}", ln=True)
        pdf.cell(100, 8, f"Time: {order.created_at.strftime('%I:%M %p')}", ln=True)
        pdf.ln(5)

        # ---------- CUSTOMER DETAILS ----------
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(190, 8, "Customer Details", ln=True, fill=True)

        pdf.set_font("Arial", "", 12)
        pdf.cell(190, 8, f"Name: {order.customer_name}", ln=True)
        pdf.cell(190, 8, f"Email: {order.customer_email}", ln=True)
        pdf.cell(190, 8, f"Phone: {order.customer_phone}", ln=True)
        pdf.multi_cell(190, 8, f"Address: {order.customer_address}")
        pdf.ln(4)

        # ---------- TABLE HEADER ----------
        pdf.set_font("Arial", "B", 12)
        pdf.set_fill_color(214, 40, 40)
        pdf.set_text_color(255, 255, 255)

        pdf.cell(80, 10, "Item", border=1, fill=True)
        pdf.cell(30, 10, "Qty", border=1, fill=True, align="C")
        pdf.cell(40, 10, "Price (Rs.)", border=1, fill=True, align="R")
        pdf.cell(40, 10, "Subtotal", border=1, fill=True, ln=True, align="R")

        # ---------- ITEMS ----------
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)

        total_price = 0

        for item in items:
            product = Product.query.get(item.product_id)
            name = product.name if product else "Deleted Item"
            subtotal = item.quantity * item.price
            total_price += subtotal

            pdf.cell(80, 10, name, border=1)
            pdf.cell(30, 10, str(item.quantity), border=1, align="C")
            pdf.cell(40, 10, f"Rs. {item.price}", border=1, align="R")
            pdf.cell(40, 10, f"Rs. {subtotal}", border=1, ln=True, align="R")

        # ---------- TOTAL ----------
        pdf.ln(5)
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(214, 40, 40)
        pdf.cell(150, 10, "TOTAL AMOUNT", border=1)
        pdf.cell(40, 10, f"Rs. {total_price}", border=1, ln=True, align="R")
        pdf.ln(5)

        # ---------- PAYMENT INFO ----------
        pdf.set_font("Arial", "", 12)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(190, 8, f"Payment Method: {order.payment_method}", ln=True)
        pdf.cell(190, 8, f"Payment Status: {order.payment_status.upper()}", ln=True)
        pdf.ln(10)

        # ---------- FOOTER ----------
        pdf.set_font("Arial", "I", 12)
        pdf.set_text_color(100, 100, 100)
        pdf.multi_cell(
            190, 8,
            "Thank you for shopping with Chunri Store!\n"
            "For support: support@chunri.store"
        )

        # ---------- RETURN PDF ----------
        pdf_data = pdf.output(dest='S').encode('latin1')
        return send_file(
            io.BytesIO(pdf_data),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"invoice_{order_id}.pdf"
        )

    except Exception as e:
        print("INVOICE ERROR:", e)
        return {"error": "Failed to generate invoice"}, 500

# ---------------------- ADMIN: GET ALL ORDERS -----------------------
@order_bp.get("/admin/orders")
@cross_origin()
def get_all_orders():
    orders = Order.query.order_by(Order.id.desc()).all()
    output = []

    for o in orders:
        items = OrderItem.query.filter_by(order_id=o.id).all()

        output.append({
            "order_id": o.id,
            "user_id": o.user_id,
            "total_price": o.total_price,
            "payment_status": o.payment_status,
            "payment_method": o.payment_method,
            "customer_name": o.customer_name,
            "customer_email": o.customer_email,
            "customer_phone": o.customer_phone,
            "customer_address": o.customer_address,
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


