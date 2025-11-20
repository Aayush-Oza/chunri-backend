from . import db
from datetime import datetime

class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    otp = db.Column(db.String(6))
    expires_at = db.Column(db.DateTime, default=datetime.utcnow)
