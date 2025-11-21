from . import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    description = db.Column(db.Text)
    price = db.Column(db.Float)
    stock = db.Column(db.Integer)
    cloth_type = db.Column(db.String(50))
    design = db.Column(db.String(50))
    size = db.Column(db.String(50))
    color = db.Column(db.String(50))
    image_url = db.Column(db.String(255))

    # SOFT DELETE FLAG
    is_active = db.Column(db.Boolean, default=True)
