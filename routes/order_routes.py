from flask import Blueprint, request, send_file
from models import db, Order, OrderItem, Product
from fpdf import FPDF
from utils.email_helper import send_email

order_bp = Blueprint("order", __name__)


# -----------------------------------------------------
# SAFE CHECKOUT (CANNOT CRASH + RETURNS CORS ALWAYS)
# -----------------------------------------------------
@order_bp.post("/checkout")
def checkout():
    try:
        data = request.json or {}

        user_id = data.get("user_id")
        name = data.get("name", "Unknown Customer")
        email = data.get("email", "no-email")
        phone = data.get("phone", "no-phone")
        address = data.get("address", "no-address")
        payment = data.get("payment", "Unknown")
        items = data.get("items", [])

        # VALIDATION
        if not user_id:
            return {"error": "user_id is required"}, 400

        if not items:
            return {"error": "No items found"}, 400

        # CREATE ORDER
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

        for item in items:
            product_id = item.get("product_id")
            qty = item.get("qty", 1)

            if not product_id:
                continue

            product = Product.query.get(product_id)
            if not product:
                continue

            subtotal = product.price * qty
            total_amount += subtotal

            order_item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=qty,
                price=product.price
            )

            db.session.add(order_item)

        order.total_price = total_amount
        db.session.commit()

        # SEND EMAIL (SAFE)
        try:
            send_email(
                to=email,
                subject="Your Chunri Store Order is Confirmed!",
                body=f"""
Hello {name},

Thank you for shopping with Chunri Store!

Order ID: {order.id}
Total Amount: ₹{total_amount}
Payment Method: {payment}

Your order will be shipped soon.

Thank You,
Chunri Store
"""
            )
        except Exception as e:
            print("Email Error:", e)

        return {
            "message": "Order placed successfully",
            "order_id": order.id,
            "total_amount": total_amount
        }

    except Exception as e:
        print("CHECKOUT ERROR:", e)
        return {"error": "Server crashed"}, 500



# -----------------------------------------------------
# GET USER ORDERS
# -----------------------------------------------------
@order_bp.get("/orders/<int:user_id>")
def get_user_orders(user_id):
    try:
        orders = Order.query.filter_by(user_id=user_id).all()
        response = []

        for o in orders:
            items = OrderItem.query.filter_by(order_id=o.id).all()

            response.append({
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

        return response

    except Exception as e:
        print("ORDER FETCH ERROR:", e)
        return {"error": "Failed to fetch orders"}, 500



# -----------------------------------------------------
# DOWNLOAD INVOICE
# -----------------------------------------------------
@order_bp.get("/invoice/<int:order_id>")
def download_invoice(order_id):
    try:
        order = Order.query.get(order_id)
        items = OrderItem.query.filter_by(order_id=order_id).all()

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=14)

        pdf.cell(200, 10, txt="Chunri Store Invoice", ln=True, align="C")
        pdf.ln(5)

        pdf.cell(200, 10, txt=f"Order ID: {order.id}", ln=True)
        pdf.cell(200, 10, txt=f"Total: ₹{order.total_price}", ln=True)
        pdf.cell(200, 10, txt=f"Payment: {order.payment_method}", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", size=12)
        pdf.cell(80, 10, txt="Item", border=1)
        pdf.cell(30, 10, txt="Qty", border=1)
        pdf.cell(30, 10, txt="Price", border=1)
        pdf.cell(50, 10, txt="Subtotal", border=1, ln=True)

        for item in items:
            product = Product.query.get(item.product_id)
            name = product.name if product else "Unknown"
            subtotal = item.quantity * item.price

            pdf.cell(80, 10, txt=name, border=1)
            pdf.cell(30, 10, txt=str(item.quantity), border=1)
            pdf.cell(30, 10, txt=str(item.price), border=1)
            pdf.cell(50, 10, txt=str(subtotal), border=1, ln=True)

        filename = f"invoice_{order_id}.pdf"
        pdf.output(filename)

        return send_file(filename, as_attachment=True)

    except Exception as e:
        print("INVOICE ERROR:", e)
        return {"error": "Failed to generate invoice"}, 500
