from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.models import Product, User

web_bp = Blueprint("web", __name__)


def _create_default_products(user_id: int) -> None:
    demo_products = [
        Product(name="智能水杯", category="家居", sales_amount=12800.0, owner_id=user_id),
        Product(name="蓝牙耳机", category="数码", sales_amount=35600.0, owner_id=user_id),
        Product(name="轻运动外套", category="服饰", sales_amount=22400.0, owner_id=user_id),
    ]
    db.session.add_all(demo_products)
    db.session.commit()


def _dashboard_context():
    products = Product.query.filter_by(owner_id=current_user.id).order_by(Product.id.asc()).all()
    total_sales = sum(item.sales_amount for item in products)
    return {
        "user": current_user,
        "products": products,
        "total_sales": total_sales,
        "product_count": len(products),
    }


@web_bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login_page"))


@web_bp.route("/register-page", methods=["GET", "POST"])
def register_page():
    if request.method == "GET":
        return render_template("register.html", error=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    if not username or len(password) < 6:
        return render_template("register.html", error="用户名不能为空，密码至少6位"), 400
    if User.query.filter_by(username=username).first():
        return render_template("register.html", error="用户名已存在"), 409

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    _create_default_products(user.id)
    login_user(user)
    return redirect(url_for("web.dashboard"))


@web_bp.route("/login-page", methods=["GET", "POST"])
def login_page():
    if request.method == "GET":
        return render_template("login.html", error=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return render_template("login.html", error="账号或密码错误"), 401

    login_user(user)
    return redirect(url_for("web.dashboard"))


@web_bp.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", **_dashboard_context(), error=None)


@web_bp.post("/products")
@login_required
def create_product():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip() or "默认分类"
    sales_text = request.form.get("sales_amount", "0").strip()

    try:
        sales_amount = float(sales_text)
    except ValueError:
        return render_template("dashboard.html", **_dashboard_context(), error="销售额必须是数字"), 400

    if not name:
        return render_template("dashboard.html", **_dashboard_context(), error="商品名称不能为空"), 400
    if sales_amount < 0:
        return render_template("dashboard.html", **_dashboard_context(), error="销售额不能为负数"), 400

    product = Product(
        name=name,
        category=category,
        sales_amount=sales_amount,
        owner_id=current_user.id,
    )
    db.session.add(product)
    db.session.commit()
    return redirect(url_for("web.dashboard"))


@web_bp.post("/products/<int:product_id>/update")
@login_required
def update_product_sales(product_id: int):
    product = db.session.get(Product, product_id)
    if product is None or product.owner_id != current_user.id:
        abort(404)

    sales_text = request.form.get("sales_amount", "0").strip()
    try:
        sales_amount = float(sales_text)
    except ValueError:
        return render_template("dashboard.html", **_dashboard_context(), error="销售额必须是数字"), 400

    if sales_amount < 0:
        return render_template("dashboard.html", **_dashboard_context(), error="销售额不能为负数"), 400

    product.sales_amount = sales_amount
    db.session.commit()
    return redirect(url_for("web.dashboard"))


@web_bp.post("/products/<int:product_id>/delete")
@login_required
def delete_product(product_id: int):
    product = db.session.get(Product, product_id)
    if product is None or product.owner_id != current_user.id:
        abort(404)

    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("web.dashboard"))


@web_bp.post("/logout-page")
@login_required
def logout_page():
    logout_user()
    return redirect(url_for("web.index"))
