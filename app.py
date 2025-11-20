from flask import Flask
from config import Config
from models import db
from flask_cors import CORS
from flask_migrate import Migrate

from routes.auth_routes import auth_bp
from routes.product_routes import product_bp
from routes.cart_routes import cart_bp
from routes.order_routes import order_bp
from routes.admin_routes import admin_bp
from routes.analytics_routes import analytics_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # GLOBAL CORS (SAFE)
    CORS(app)

    db.init_app(app)
    Migrate(app, db)

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(product_bp, url_prefix="/api")
    app.register_blueprint(cart_bp, url_prefix="/api")
    app.register_blueprint(order_bp, url_prefix="/api")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(analytics_bp, url_prefix="/admin")

    @app.route("/")
    def home():
        return {"message": "Chunri Backend Running"}

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

