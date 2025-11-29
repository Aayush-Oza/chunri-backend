from flask import Blueprint, request
from models import db, User, OTP
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import cross_origin
import random
import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()   # Only for local. Render ignores this.

auth_bp = Blueprint("auth", __name__)

# ----------------------------------------------------
# ADMIN LOGIN
# ----------------------------------------------------
ADMIN_EMAIL = "Pkumawat27@121.com"
ADMIN_PASSWORD = "Pkumawat@121"


# ----------------------------------------------------
# GMAIL SMTP EMAIL SENDER (SSL - PORT 465)
# ----------------------------------------------------
def send_email(to, subject, body):
    smtp_server = os.getenv("SMTP_SERVER")   # smtp.gmail.com
    smtp_port = int(os.getenv("SMTP_PORT"))  # 587 (RECOMMENDED)
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    message = f"Subject: {subject}\n\n{body}"

    # --------- IF USING PORT 587 (STARTTLS) ----------
    if smtp_port == 587:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls(context=context)
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to, message)
        return True

    # --------- IF USING PORT 465 (SSL) ----------
    elif smtp_port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to, message)
        return True

    else:
        raise ValueError("Invalid SMTP Port (must be 465 or 587)")



# ----------------------------------------------------
# SEND OTP
# ----------------------------------------------------
@auth_bp.route("/send-otp", methods=["POST", "OPTIONS"])
@cross_origin()
def send_otp():
    if request.method == "OPTIONS":
        return {}, 200

    data = request.json or {}
    email = data.get("email")

    if not email or not isinstance(email, str) or email.strip() == "":
        return {"error": "Invalid email"}, 400

    OTP.query.filter_by(email=email).delete()
    db.session.commit()

    otp = str(random.randint(100000, 999999))
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

    record = OTP(email=email, otp=otp, expires_at=expiry)
    db.session.add(record)
    db.session.commit()

    ok = send_email(email, "Chunri Store OTP", f"Your OTP is: {otp}")
    if not ok:
        return {"error": "Failed to send email"}, 500

    return {"message": "OTP sent successfully"}


# ----------------------------------------------------
# VERIFY OTP
# ----------------------------------------------------
@auth_bp.route("/verify-otp", methods=["POST", "OPTIONS"])
@cross_origin()
def verify_otp():
    if request.method == "OPTIONS":
        return {}, 200

    data = request.json
    email = data["email"]
    otp = data["otp"]

    record = OTP.query.filter_by(email=email).first()

    if not record:
        return {"error": "OTP not generated"}, 400

    if record.expires_at < datetime.datetime.utcnow():
        return {"error": "OTP expired"}, 400

    if record.otp != otp:
        return {"error": "Invalid OTP"}, 400

    return {"verified": True}


# ----------------------------------------------------
# REGISTER
# ----------------------------------------------------
@auth_bp.route("/register", methods=["POST", "OPTIONS"])
@cross_origin()
def register():
    if request.method == "OPTIONS":
        return {}, 200

    data = request.json
    otp_record = OTP.query.filter_by(email=data["email"]).first()

    if not otp_record:
        return {"error": "OTP not verified"}, 400

    user = User(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        address=data["address"]
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    OTP.query.filter_by(email=data["email"]).delete()
    db.session.commit()

    return {"message": "User registered successfully"}


# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------
@auth_bp.route("/login", methods=["POST", "OPTIONS"])
@cross_origin()
def login():
    if request.method == "OPTIONS":
        return {}, 200

    try:
        data = request.json
        email = data["email"]
        password = data["password"]

        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            return {
                "message": "Admin login successful",
                "user_id": 0,
                "is_admin": True
            }

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"error": "Invalid credentials"}, 401

        return {
            "message": "Login successful",
            "user_id": user.id,
            "is_admin": user.is_admin
        }

    except Exception as e:
        print("LOGIN ERROR:", e)
        return {"error": "Internal Server Error"}, 500


# ----------------------------------------------------
# GET PROFILE
# ----------------------------------------------------
@auth_bp.route("/profile/<int:user_id>", methods=["GET", "OPTIONS"])
@cross_origin()
def get_profile(user_id):
    if request.method == "OPTIONS":
        return {}, 200

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "address": user.address,
        "is_admin": user.is_admin
    }


# ----------------------------------------------------
# UPDATE PROFILE
# ----------------------------------------------------
@auth_bp.route("/profile/update/<int:user_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def update_profile(user_id):
    if request.method == "OPTIONS":
        return {}, 200

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    data = request.json
    for field in ["name", "email", "phone", "address"]:
        if field in data:
            setattr(user, field, data[field])

    db.session.commit()
    return {"message": "Profile updated successfully"}


# ----------------------------------------------------
# CHANGE PASSWORD
# ----------------------------------------------------
@auth_bp.route("/profile/change-password/<int:user_id>", methods=["PUT", "OPTIONS"])
@cross_origin()
def change_password(user_id):
    if request.method == "OPTIONS":
        return {}, 200

    user = User.query.get(user_id)
    if not user:
        return {"error": "User not found"}, 404

    data = request.json
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not user.check_password(old_password):
        return {"error": "Incorrect old password"}, 400

    user.set_password(new_password)
    db.session.commit()

    return {"message": "Password updated successfully"}

