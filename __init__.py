from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .product import Product
from .order import Order
from .order_item import OrderItem
from .cart import Cart
from .otp import OTP
