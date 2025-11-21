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


# ---------------------- INVOICE DOWNLOAD -----------------------
# ---------------------- PROFESSIONAL INVOICE DOWNLOAD -----------------------
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
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Chunri Store", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 6, "Official Invoice", ln=True, align="C")
        pdf.ln(8)

        # ---------- ORDER DETAILS ----------
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Order Details", ln=True)

        pdf.set_font("Arial", "", 11)
        pdf.cell(100, 6, f"Order ID: {order.id}", ln=True)
        pdf.cell(100, 6, f"Order Date: {order.created_at.strftime('%d %b %Y, %I:%M %p')}", ln=True)
        pdf.cell(100, 6, f"Payment Method: {order.payment_method}", ln=True)
        pdf.cell(100, 6, f"Payment Status: {order.payment_status.capitalize()}", ln=True)

        pdf.ln(4)

        # ---------- CUSTOMER DETAILS ----------
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Customer Information", ln=True)

        pdf.set_font("Arial", "", 11)
        pdf.cell(100, 6, f"Name: {order.customer_name}", ln=True)
        pdf.cell(100, 6, f"Email: {order.customer_email}", ln=True)
        pdf.cell(100, 6, f"Phone: {order.customer_phone}", ln=True)
        pdf.multi_cell(0, 6, f"Address: {order.customer_address}", ln=True)

        pdf.ln(4)

        # ---------- ORDER ITEMS TABLE ----------
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Ordered Items", ln=True)

        # Table Header
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(80, 8, "Item", border=1, fill=True)
        pdf.cell(20, 8, "Qty", border=1, fill=True)
        pdf.cell(30, 8, "Price", border=1, fill=True)
        pdf.cell(40, 8, "Subtotal", border=1, fill=True, ln=True)

        # Table Rows
        pdf.set_font("Arial", "", 10)
        total = 0
        for item in items:
            product = Product.query.get(item.product_id)
            name = product.name if product else "Unknown Item"

            qty = item.quantity
            price = item.price
            subtotal = qty * price
            total += subtotal

            pdf.cell(80, 8, name, border=1)
            pdf.cell(20, 8, str(qty), border=1)
            pdf.cell(30, 8, f"₹{price}", border=1)
            pdf.cell(40, 8, f"₹{subtotal}", border=1, ln=True)

        pdf.ln(4)

        # ---------- TOTAL ----------
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, f"Grand Total: ₹{total}", ln=True)

        # ---------- FOOTER ----------
        pdf.ln(10)
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 6, "Thank you for shopping with Chunri Store!", ln=True, align="C")

        # OUTPUT
        pdf_buffer = io.BytesIO()
        pdf.output(pdf_buffer)
        pdf_buffer.seek(0)

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"invoice_{order_id}.pdf"
        )

    except Exception as e:
        print("INVOICE PDF ERROR:", e)
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
