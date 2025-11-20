from flask import Blueprint, request
from models import db, User, OTP
from werkzeug.security import generate_password_hash, check_password_hash
import random
import datetime
import smtplib
from email.mime.text import MIMEText

auth_bp = Blueprint("auth", __name__)

# ----------------------------------------------------
# ADMIN LOGIN
# ----------------------------------------------------
ADMIN_EMAIL = "Pkumawat27@121.com"
ADMIN_PASSWORD = "Pkumawat@121"


# ----------------------------------------------------
# EMAIL SENDER (GMAIL SMTP)
# ----------------------------------------------------
def send_email(to, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "aayushoza2006@gmail.com"      # your gmail
    smtp_password = "ocsjcyvziusorfuw"         # app password

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to, msg.as_string())
        server.quit()
        print("EMAIL SENT:", to)
    except Exception as e:
        print("EMAIL FAILED:", e)


# ----------------------------------------------------
# SEND OTP
# ----------------------------------------------------
@auth_bp.post("/send-otp")
def send_otp():
    data = request.json
    email = data["email"]
    phone = data.get("phone")

    # Delete old OTP
    OTP.query.filter_by(email=email).delete()
    db.session.commit()

    otp = str(random.randint(100000, 999999))
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)

    record = OTP(email=email, phone=phone, otp=otp, expires_at=expiry)
    db.session.add(record)
    db.session.commit()

    # Send via email
    send_email(email, "Chunri Store OTP", f"Your OTP is: {otp}")

    print(f"OTP for {email}: {otp}")
    return {"message": "OTP sent successfully"}


# ----------------------------------------------------
# VERIFY OTP
# ----------------------------------------------------
@auth_bp.post("/verify-otp")
def verify_otp():
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
# REGISTER (AFTER OTP)
# ----------------------------------------------------
@auth_bp.post("/register")
def register():
    data = request.json

    # Check if OTP exists for this email
    otp_record = OTP.query.filter_by(email=data["email"]).first()
    if not otp_record:
        return {"error": "OTP not verified"}, 400

    # Create user
    user = User(
        name=data["name"],
        email=data["email"],
        phone=data["phone"],
        address=data["address"]
    )

    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    # Remove OTP after registration
    OTP.query.filter_by(email=data["email"]).delete()
    db.session.commit()

    return {"message": "User registered successfully"}


# ----------------------------------------------------
# LOGIN
# ----------------------------------------------------
@auth_bp.post("/login")
def login():
    data = request.json
    email = data["email"]
    password = data["password"]

    # Admin login
    if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
        return {
            "message": "Admin login successful",
            "user_id": 0,
            "is_admin": True
        }

    # User login
    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return {"error": "Invalid credentials"}, 401

    return {
        "message": "Login successful",
        "user_id": user.id,
        "is_admin": user.is_admin
    }
