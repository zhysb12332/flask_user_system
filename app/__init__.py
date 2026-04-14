from flask import Flask, jsonify
from flask_cors import CORS

from app.auth import auth_bp
from app.extensions import db, login_manager
from app.web import web_bp
from config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "web.login_page"

    app.register_blueprint(auth_bp)
    app.register_blueprint(web_bp)

    @app.get("/api/v1/health")
    def health():
        return jsonify({"ok": True, "message": "service is running"})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"ok": False, "message": "not found"}), 404

    with app.app_context():
        db.create_all()

    return app
