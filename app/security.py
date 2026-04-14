from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.models import User


def _serializer(secret_key: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(secret_key=secret_key, salt="auth-token")


def generate_token(user: User, secret_key: str) -> str:
    return _serializer(secret_key).dumps({"uid": user.id})


def verify_token(token: str, secret_key: str, max_age: int):
    try:
        data = _serializer(secret_key).loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    user_id = data.get("uid")
    if not isinstance(user_id, int):
        return None
    return user_id
