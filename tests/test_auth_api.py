from app import create_app
from app.extensions import db
from app.models import Product, User, load_user
from app.security import _serializer, generate_token, verify_token
from config import TestConfig


def _register(client, username="alice", password="secret1"):
    return client.post(
        "/api/v1/auth/register", json={"username": username, "password": password}
    )


def _login(client, username="alice", password="secret1"):
    return client.post(
        "/api/v1/auth/login", json={"username": username, "password": password}
    )


def test_auth_flow_and_edge_cases():
    app = create_app(TestConfig)
    client = app.test_client()

    with app.app_context():
        assert load_user("abc") is None

    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True

    resp = _register(client, username="", password="123")
    assert resp.status_code == 400

    resp = _register(client)
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["user"]["username"] == "alice"

    resp = _register(client)
    assert resp.status_code == 409

    resp = _login(client, password="bad")
    assert resp.status_code == 401
    resp = _login(client, username="nobody")
    assert resp.status_code == 401

    resp = _login(client)
    assert resp.status_code == 200
    token = resp.get_json()["token"]

    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200

    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 200

    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401

    resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Token abc"})
    assert resp.status_code == 401

    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401

    with app.app_context():
        user = User.query.filter_by(username="alice").first()
        broken = generate_token(user, app.config["SECRET_KEY"])
        assert verify_token(broken + "x", app.config["SECRET_KEY"], 10) is None
        bad_uid_token = _serializer(app.config["SECRET_KEY"]).dumps({"uid": "bad"})
        assert verify_token(bad_uid_token, app.config["SECRET_KEY"], 10) is None

    with app.app_context():
        user = User.query.filter_by(username="alice").first()
        short_token = generate_token(user, app.config["SECRET_KEY"])
    # Use a negative max_age to deterministically trigger expiration branch.
    assert verify_token(short_token, app.config["SECRET_KEY"], -1) is None

    with app.app_context():
        db.session.add(User(username="temp", password_hash="x"))
        db.session.commit()
        user = User.query.filter_by(username="temp").first()
        assert user.to_dict()["username"] == "temp"
        assert user.check_password("x") is False
        user.set_password("abc123")
        db.session.commit()
        assert user.check_password("abc123") is True
        assert load_user(str(user.id)).username == "temp"

    resp = client.post("/api/v1/auth/logout")
    assert resp.status_code == 401

    resp = client.get("/missing")
    assert resp.status_code == 404


def test_web_pages_flow_and_errors():
    app = create_app(TestConfig)
    client = app.test_client()

    resp = client.get("/")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/login-page")

    resp = client.get("/register-page")
    assert resp.status_code == 200
    assert "注册并登录".encode("utf-8") in resp.data
    resp = client.post("/register-page", data={"username": "", "password": "123"})
    assert resp.status_code == 400
    resp = client.post("/register-page", data={"username": "webu", "password": "123456"})
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]

    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert "webu".encode("utf-8") in resp.data
    assert "商品列表".encode("utf-8") in resp.data
    assert "蓝牙耳机".encode("utf-8") in resp.data
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]

    with app.app_context():
        products = Product.query.filter_by(owner_id=User.query.filter_by(username="webu").first().id).all()
        assert len(products) == 3

    resp = client.post("/logout-page")
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")

    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]

    resp = client.get("/login-page")
    assert resp.status_code == 200
    resp = client.post("/login-page", data={"username": "webu", "password": "bad"})
    assert resp.status_code == 401
    resp = client.post("/login-page", data={"username": "webu", "password": "123456"})
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]

    resp = client.post("/products", data={"name": "", "category": "数码", "sales_amount": "10"})
    assert resp.status_code == 400
    resp = client.post("/products", data={"name": "随身风扇", "category": "家居", "sales_amount": "bad"})
    assert resp.status_code == 400
    resp = client.post("/products", data={"name": "随身风扇", "category": "家居", "sales_amount": "-1"})
    assert resp.status_code == 400
    resp = client.post("/products", data={"name": "随身风扇", "category": "家居", "sales_amount": "9800"})
    assert resp.status_code == 302

    with app.app_context():
        user = User.query.filter_by(username="webu").first()
        product = Product.query.filter_by(owner_id=user.id, name="随身风扇").first()
        assert product.to_dict()["category"] == "家居"
        product_id = product.id

    resp = client.post(f"/products/{product_id}/update", data={"sales_amount": "oops"})
    assert resp.status_code == 400
    resp = client.post(f"/products/{product_id}/update", data={"sales_amount": "-10"})
    assert resp.status_code == 400
    resp = client.post(f"/products/{product_id}/update", data={"sales_amount": "15000"})
    assert resp.status_code == 302

    with app.app_context():
        updated = db.session.get(Product, product_id)
        assert updated.sales_amount == 15000

    resp = client.post("/products/999/update", data={"sales_amount": "100"})
    assert resp.status_code == 404

    resp = client.post(f"/products/{product_id}/delete")
    assert resp.status_code == 302
    with app.app_context():
        assert db.session.get(Product, product_id) is None

    resp = client.post("/products/999/delete")
    assert resp.status_code == 404

    # duplicate username branch in page registration
    client.post("/logout-page")
    resp = client.post("/register-page", data={"username": "webu", "password": "123456"})
    assert resp.status_code == 409
