from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.models import User
from app.security import generate_token, verify_token

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


def _json_error(message: str, status: int):
    return jsonify({"ok": False, "message": message}), status


def _token_from_header():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header[7:].strip()


def _resolve_user():
    if current_user.is_authenticated:
        return current_user

    token = _token_from_header()
    if not token:
        return None

    user_id = verify_token(
        token=token,
        secret_key=current_app.config["SECRET_KEY"],
        max_age=current_app.config["TOKEN_MAX_AGE"],
    )
    if user_id is None:
        return None
    return db.session.get(User, user_id)


@auth_bp.post("/register")
def register():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or len(password) < 6:
        return _json_error("username required and password length >= 6", 400)

    if User.query.filter_by(username=username).first():
        return _json_error("username already exists", 409)

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return _json_error("invalid username or password", 401)

    login_user(user)
    token = generate_token(user, current_app.config["SECRET_KEY"])
    return jsonify({"ok": True, "token": token, "user": user.to_dict()})


@auth_bp.post("/logout")
def logout():
    user = _resolve_user()
    if not user:
        return _json_error("unauthorized", 401)

    if current_user.is_authenticated:
        logout_user()
    return jsonify({"ok": True, "message": "logged out"})


@auth_bp.get("/me")
def me():
    user = _resolve_user()
    if not user:
        return _json_error("unauthorized", 401)
    return jsonify({"ok": True, "user": user.to_dict()})
