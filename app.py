
from flask import Flask, render_template, request, redirect, url_for, session, flash
from decimal import Decimal
import os

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-this")

PRODUCTS = [
    {
        "id": "p1",
        "title": "Еко-інфузор для заварювання чаю",
        "description": "Нержавіючий інфузор для заварювання чаю, підходить для будь-яких сортів. Матеріал: нержавіюча сталь. Об'єм: 80 мл.",
        "price": Decimal("249.00"),
        "currency": "UAH",
        "mcc": "5977",
        "manufacturer": "EcoTea Co., Україна",
        "category": "household",
        "image": ""
    },
    {
        "id": "p2",
        "title": "Натуральний мед 500 г",
        "description": "Мед акацієвий, без домішок. Вага: 500 г. Виробник: HoneyLand, Україна.",
        "price": Decimal("199.00"),
        "currency": "UAH",
        "mcc": "5499",
        "manufacturer": "HoneyLand, Україна",
        "category": "food",
        "image": ""
    },
    {
        "id": "p3",
        "title": "Подарунковий сертифікат на 500 UAH",
        "description": "Електронний сертифікат дійсний 12 місяців. Після покупки покупець отримає код на вказаний e-mail.",
        "price": Decimal("500.00"),
        "currency": "UAH",
        "mcc": "4829",
        "manufacturer": "MerchantUA (digital)",
        "category": "digital",
        "image": ""
    }
]

FORBIDDEN_CATEGORIES = [
    "азартні ігри",
    "обмін віртуальних активів",
    "мікрокредитні агрегатори",
    "форекс",
    "трейдинг",
    "інвестиційні проекти"
]

def get_product(pid):
    return next((p for p in PRODUCTS if p["id"] == pid), None)

def init_cart():
    if "cart" not in session:
        session["cart"] = {}

def cart_items():
    init_cart()
    items = []
    for pid, qty in session["cart"].items():
        prod = get_product(pid)
        if prod:
            items.append({"product": prod, "quantity": qty, "line_total": prod["price"] * qty})
    return items

def cart_total():
    total = Decimal("0.00")
    for it in cart_items():
        total += it["line_total"]
    return total

def validate_category(cat_value):
    if not cat_value:
        return True
    c = cat_value.lower()
    for f in FORBIDDEN_CATEGORIES:
        if f in c:
            return False
    return True

@app.context_processor
def inject_globals():
    return dict(PRODUCTS=PRODUCTS, current_year=2025)

@app.route("/")
def home():
    init_cart()
    featured = PRODUCTS[:3]
    return render_template("home.html", products=featured, cart_count=sum(session["cart"].values()))

@app.route("/catalog")
def catalog():
    init_cart()
    return render_template("catalog.html", products=PRODUCTS, cart_count=sum(session["cart"].values()))

@app.route("/product/<product_id>")
def product_detail(product_id):
    init_cart()
    p = get_product(product_id)
    if not p:
        return render_template("404.html"), 404
    return render_template("product.html", product=p, cart_count=sum(session["cart"].values()))

@app.route("/cart")
def view_cart():
    init_cart()
    items = cart_items()
    return render_template("cart.html", items=items, total=cart_total(), cart_count=sum(session["cart"].values()))

@app.route("/cart/add/<product_id>", methods=["POST", "GET"])
def add_to_cart(product_id):
    init_cart()
    qty = int(request.form.get("quantity", 1)) if request.method == "POST" else 1
    if product_id not in session["cart"]:
        session["cart"][product_id] = qty
    else:
        session["cart"][product_id] += qty
    session.modified = True
    flash("Товар додано до кошика.", "success")
    return redirect(request.referrer or url_for("catalog"))

@app.route("/cart/remove/<product_id>")
def remove_from_cart(product_id):
    init_cart()
    if product_id in session["cart"]:
        session["cart"].pop(product_id)
        session.modified = True
    return redirect(url_for("view_cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    init_cart()
    items = cart_items()
    if request.method == "POST":
        order = {
            "name": request.form.get("name"),
            "email": request.form.get("email"),
            "phone": request.form.get("phone"),
            "address": request.form.get("address"),
            "items": items,
            "total": float(cart_total())
        }
        session.pop("cart", None)
        flash("Дякуємо! Замовлення прийнято. Менеджер зв'яжеться з вами для подальших інструкцій щодо оплати.", "info")
        return redirect(url_for("home"))
    return render_template("checkout.html", items=items, total=cart_total(), cart_count=sum(session["cart"].values()))

@app.route("/terms")
def terms():
    init_cart()
    return render_template("terms.html", cart_count=sum(session["cart"].values()))

@app.route("/privacy")
def privacy():
    init_cart()
    return render_template("privacy.html", cart_count=sum(session["cart"].values()))

@app.route("/contacts")
def contacts():
    init_cart()
    return render_template("contacts.html", cart_count=sum(session["cart"].values()))

@app.route("/manufacturer")
def manufacturer():
    init_cart()
    return render_template("manufacturer.html", cart_count=sum(session["cart"].values()))

@app.route("/security")
def security():
    init_cart()
    return render_template("security.html", cart_count=sum(session["cart"].values()))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    init_cart()
    if request.method == "POST":
        new = {
            "id": request.form.get("id") or f"p{len(PRODUCTS)+1}",
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "price": Decimal(request.form.get("price") or "0"),
            "currency": request.form.get("currency") or "UAH",
            "mcc": request.form.get("mcc") or "",
            "manufacturer": request.form.get("manufacturer") or "",
            "category": request.form.get("category") or "",
            "image": request.form.get("image") or ""
        }
        if not validate_category(new["category"]):
            flash("Категорія заборонена політикою платіжного мерчанту. Вкажіть іншу категорію.", "danger")
            return redirect(url_for("admin"))
        PRODUCTS.append(new)
        flash("Товар додано успішно.", "success")
        return redirect(url_for("catalog"))
    return render_template("admin.html", products=PRODUCTS, forbidden=FORBIDDEN_CATEGORIES, cart_count=sum(session["cart"].values()))

@app.route("/dev/clear")
def dev_clear():
    session.clear()
    flash("Сесія очищена (розробницька функція).", "info")
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True, port=5000)
