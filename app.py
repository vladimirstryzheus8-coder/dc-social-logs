from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify
)

from functools import wraps
from database import get_db, create_tables

import os
import uuid


# =========================================================
# DC SOCIAL LOGS 🪵
# MAIN FLASK APPLICATION
# =========================================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "dc-social-logs-change-this-secret-key"
)

create_tables()


# =========================================================
# AUTHENTICATION HELPERS
# =========================================================

def login_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login to continue.", "info")
            return redirect(url_for("login"))

        return function(*args, **kwargs)

    return decorated_function


def admin_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first.", "info")
            return redirect(url_for("login"))

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users
            WHERE id = ?
        """, (session["user_id"],)).fetchone()

        conn.close()

        if not user or user["is_admin"] != 1:
            flash("Administrator access required.", "error")
            return redirect(url_for("home"))

        return function(*args, **kwargs)

    return decorated_function


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    conn = get_db()

    categories = conn.execute("""
        SELECT *
        FROM categories
        WHERE is_active = 1
        ORDER BY id ASC
    """).fetchall()

    products = conn.execute("""
        SELECT
            products.*,
            categories.name AS category_name,

            (
                SELECT COUNT(*)
                FROM stock
                WHERE stock.product_id = products.id
                AND stock.status = 'available'
            ) AS stock_count

        FROM products

        JOIN categories
            ON categories.id = products.category_id

        WHERE products.is_active = 1

        ORDER BY products.featured DESC, products.id DESC

        LIMIT 12
    """).fetchall()

    conn.close()

    return render_template(
        "index.html",
        categories=categories,
        products=products
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        phone = request.form.get("phone", "").strip()

        if not username or not email or not password:

            flash(
                "Username, email and password are required.",
                "error"
            )

            return render_template("register.html")

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return render_template("register.html")

        conn = get_db()

        existing_user = conn.execute("""
            SELECT id
            FROM users
            WHERE username = ?
               OR email = ?
        """, (
            username,
            email
        )).fetchone()

        if existing_user:

            conn.close()

            flash(
                "Username or email already exists.",
                "error"
            )

            return render_template("register.html")

        conn.execute("""
            INSERT INTO users
            (
                username,
                email,
                password,
                full_name,
                phone
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            username,
            email,
            password,
            full_name,
            phone
        ))

        conn.commit()

        user = conn.execute("""
            SELECT id
            FROM users
            WHERE username = ?
        """, (username,)).fetchone()

        conn.close()

        session["user_id"] = user["id"]
        session["username"] = username

        flash(
            "Account created successfully!",
            "success"
        )

        return redirect(url_for("dashboard"))

    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        username_or_email = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        conn = get_db()

        user = conn.execute("""
            SELECT *
            FROM users

            WHERE
                (
                    username = ?
                    OR email = ?
                )

            AND password = ?
            AND is_active = 1

        """, (
            username_or_email,
            username_or_email.lower(),
            password
        )).fetchone()

        conn.close()

        if not user:

            flash(
                "Invalid login details.",
                "error"
            )

            return render_template("login.html")

        session["user_id"] = user["id"]
        session["username"] = user["username"]

        flash(
            f"Welcome back, {user['username']}!",
            "success"
        )

        return redirect(url_for("dashboard"))

    return render_template("login.html")


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(url_for("home"))


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    conn = get_db()

    user = conn.execute("""
        SELECT *
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    orders_count = conn.execute("""
        SELECT COUNT(*)
        FROM orders
        WHERE user_id = ?
    """, (user_id,)).fetchone()[0]

    total_spent = conn.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM orders
        WHERE user_id = ?
        AND payment_status = 'paid'
    """, (user_id,)).fetchone()[0]

    transactions = conn.execute("""
        SELECT *
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    orders = conn.execute("""
        SELECT *
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    """, (user_id,)).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        user=user,
        orders_count=orders_count,
        total_spent=total_spent,
        transactions=transactions,
        orders=orders
    )


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
def products():

    category_id = request.args.get(
        "category",
        type=int
    )

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db()

    query = """
        SELECT
            products.*,
            categories.name AS category_name,

            (
                SELECT COUNT(*)
                FROM stock
                WHERE stock.product_id = products.id
                AND stock.status = 'available'
            ) AS stock_count

        FROM products

        JOIN categories
            ON categories.id = products.category_id

        WHERE products.is_active = 1
    """

    params = []

    if category_id:

        query += """
            AND products.category_id = ?
        """

        params.append(category_id)

    if search:

        query += """
            AND (
                products.name LIKE ?
                OR products.description LIKE ?
            )
        """

        search_value = f"%{search}%"

        params.extend([
            search_value,
            search_value
        ])

    query += """
        ORDER BY products.featured DESC,
                 products.id DESC
    """

    products = conn.execute(
        query,
        params
    ).fetchall()

    categories = conn.execute("""
        SELECT *
        FROM categories
        WHERE is_active = 1
        ORDER BY id ASC
    """).fetchall()

    conn.close()

    return render_template(
        "products.html",
        products=products,
        categories=categories,
        selected_category=category_id,
        search=search
    )


# =========================================================
# PRODUCT DETAILS
# =========================================================

@app.route("/product/<int:product_id>")
def product_details(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT
            products.*,
            categories.name AS category_name,

            (
                SELECT COUNT(*)
                FROM stock
                WHERE stock.product_id = products.id
                AND stock.status = 'available'
            ) AS stock_count

        FROM products

        JOIN categories
            ON categories.id = products.category_id

        WHERE products.id = ?
        AND products.is_active = 1
    """, (product_id,)).fetchone()

    conn.close()

    if not product:

        flash(
            "Product not found.",
            "error"
        )

        return redirect(url_for("products"))

    return render_template(
        "product_details.html",
        product=product
    )


# =========================================================
# SUPPORT INFORMATION
# =========================================================

@app.context_processor
def inject_support():

    conn = get_db()

    support = conn.execute("""
        SELECT *
        FROM support_settings
        LIMIT 1
    """).fetchone()

    conn.close()

    return {
        "support": support
    }


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

# =========================================================
# ADMIN PANEL
# =========================================================

@app.route("/admin")
@admin_required
def admin():

    conn = get_db()

    stats = {
        "users": conn.execute(
            "SELECT COUNT(*) FROM users"
        ).fetchone()[0],

        "products": conn.execute(
            "SELECT COUNT(*) FROM products"
        ).fetchone()[0],

        "orders": conn.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0],

        "stock": conn.execute("""
            SELECT COUNT(*)
            FROM stock
            WHERE status = 'available'
        """).fetchone()[0],

        "pending_payments": conn.execute("""
            SELECT COUNT(*)
            FROM payments
            WHERE status = 'pending'
        """).fetchone()[0]
    }

    recent_orders = conn.execute("""
        SELECT
            orders.*,
            users.username
        FROM orders
        JOIN users
            ON users.id = orders.user_id
        ORDER BY orders.id DESC
        LIMIT 10
    """).fetchall()

    conn.close()

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_orders=recent_orders
    )


# =========================================================
# ADMIN - PRODUCTS
# =========================================================

@app.route("/admin/products")
@admin_required
def admin_products():

    conn = get_db()

    products = conn.execute("""
        SELECT
            products.*,
            categories.name AS category_name,

            (
                SELECT COUNT(*)
                FROM stock
                WHERE stock.product_id = products.id
                AND stock.status = 'available'
            ) AS stock_count

        FROM products

        JOIN categories
            ON categories.id = products.category_id

        ORDER BY products.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/products.html",
        products=products
    )


# =========================================================
# ADMIN - ADD PRODUCT
# =========================================================

@app.route("/admin/products/add", methods=["GET", "POST"])
@admin_required
def admin_add_product():

    conn = get_db()

    categories = conn.execute("""
        SELECT *
        FROM categories
        WHERE is_active = 1
        ORDER BY name ASC
    """).fetchall()

    if request.method == "POST":

        category_id = request.form.get(
            "category_id",
            type=int
        )

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            0,
            type=float
        )

        old_price = request.form.get(
            "old_price",
            0,
            type=float
        )

        image = request.form.get(
            "image",
            ""
        ).strip()

        delivery_type = request.form.get(
            "delivery_type",
            "automatic"
        )

        delivery_information = request.form.get(
            "delivery_information",
            ""
        ).strip()

        featured = 1 if request.form.get(
            "featured"
        ) else 0

        if not category_id or not name:

            conn.close()

            flash(
                "Category and product name are required.",
                "error"
            )

            return render_template(
                "admin/add_product.html",
                categories=categories
            )

        cursor = conn.execute("""
            INSERT INTO products
            (
                category_id,
                name,
                description,
                price,
                old_price,
                image,
                delivery_type,
                delivery_information,
                featured
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            category_id,
            name,
            description,
            price,
            old_price,
            image,
            delivery_type,
            delivery_information,
            featured
        ))

        product_id = cursor.lastrowid

        conn.commit()
        conn.close()

        flash(
            "Product created successfully.",
            "success"
        )

        return redirect(
            url_for(
                "admin_manage_stock",
                product_id=product_id
            )
        )

    conn.close()

    return render_template(
        "admin/add_product.html",
        categories=categories
    )


# =========================================================
# ADMIN - EDIT PRODUCT
# =========================================================

@app.route(
    "/admin/products/<int:product_id>/edit",
    methods=["GET", "POST"]
)
@admin_required
def admin_edit_product(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    if not product:

        conn.close()

        flash(
            "Product not found.",
            "error"
        )

        return redirect(
            url_for("admin_products")
        )

    categories = conn.execute("""
        SELECT *
        FROM categories
        ORDER BY name ASC
    """).fetchall()

    if request.method == "POST":

        category_id = request.form.get(
            "category_id",
            type=int
        )

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            0,
            type=float
        )

        old_price = request.form.get(
            "old_price",
            0,
            type=float
        )

        image = request.form.get(
            "image",
            ""
        ).strip()

        delivery_type = request.form.get(
            "delivery_type",
            "automatic"
        )

        delivery_information = request.form.get(
            "delivery_information",
            ""
        ).strip()

        featured = 1 if request.form.get(
            "featured"
        ) else 0

        is_active = 1 if request.form.get(
            "is_active"
        ) else 0

        conn.execute("""
            UPDATE products

            SET
                category_id = ?,
                name = ?,
                description = ?,
                price = ?,
                old_price = ?,
                image = ?,
                delivery_type = ?,
                delivery_information = ?,
                featured = ?,
                is_active = ?,
                updated_at = CURRENT_TIMESTAMP

            WHERE id = ?
        """, (
            category_id,
            name,
            description,
            price,
            old_price,
            image,
            delivery_type,
            delivery_information,
            featured,
            is_active,
            product_id
        ))

        conn.commit()
        conn.close()

        flash(
            "Product updated successfully.",
            "success"
        )

        return redirect(
            url_for("admin_products")
        )

    conn.close()

    return render_template(
        "admin/edit_product.html",
        product=product,
        categories=categories
    )


# =========================================================
# ADMIN - DELETE PRODUCT
# =========================================================

@app.route(
    "/admin/products/<int:product_id>/delete",
    methods=["POST"]
)
@admin_required
def admin_delete_product(product_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM products
        WHERE id = ?
    """, (product_id,))

    conn.commit()
    conn.close()

    flash(
        "Product deleted successfully.",
        "success"
    )

    return redirect(
        url_for("admin_products")
    )


# =========================================================
# ADMIN - STOCK MANAGEMENT
# =========================================================

@app.route(
    "/admin/products/<int:product_id>/stock",
    methods=["GET", "POST"]
)
@admin_required
def admin_manage_stock(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    if not product:

        conn.close()

        flash(
            "Product not found.",
            "error"
        )

        return redirect(
            url_for("admin_products")
        )

    if request.method == "POST":

        stock_text = request.form.get(
            "stock",
            ""
        )

        # Each line represents one stock item.
        stock_items = [
            line.strip()
            for line in stock_text.splitlines()
            if line.strip()
        ]

        # Allow up to 200 items in one upload.
        if len(stock_items) > 200:

            conn.close()

            flash(
                "You can add a maximum of 200 stock items at once.",
                "error"
            )

            return redirect(
                url_for(
                    "admin_manage_stock",
                    product_id=product_id
                )
            )

        for item in stock_items:

            conn.execute("""
                INSERT INTO stock
                (
                    product_id,
                    stock_content
                )
                VALUES (?, ?)
            """, (
                product_id,
                item
            ))

        conn.commit()

        flash(
            f"{len(stock_items)} stock item(s) added.",
            "success"
        )

    stock = conn.execute("""
        SELECT *
        FROM stock
        WHERE product_id = ?
        ORDER BY id DESC
    """, (product_id,)).fetchall()

    available_count = conn.execute("""
        SELECT COUNT(*)
        FROM stock
        WHERE product_id = ?
        AND status = 'available'
    """, (product_id,)).fetchone()[0]

    conn.close()

    return render_template(
        "admin/stock.html",
        product=product,
        stock=stock,
        available_count=available_count
    )


# =========================================================
# ADMIN - DELETE STOCK ITEM
# =========================================================

@app.route(
    "/admin/stock/<int:stock_id>/delete",
    methods=["POST"]
)
@admin_required
def admin_delete_stock(stock_id):

    conn = get_db()

    conn.execute("""
        DELETE FROM stock
        WHERE id = ?
    """, (stock_id,))

    conn.commit()
    conn.close()

    flash(
        "Stock item deleted.",
        "success"
    )

    return redirect(
        request.referrer or
        url_for("admin_products")
    )


# =========================================================
# ADMIN - CATEGORIES
# =========================================================

@app.route("/admin/categories")
@admin_required
def admin_categories():

    conn = get_db()

    categories = conn.execute("""
        SELECT
            categories.*,

            (
                SELECT COUNT(*)
                FROM products
                WHERE products.category_id = categories.id
            ) AS product_count

        FROM categories

        ORDER BY categories.id ASC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/categories.html",
        categories=categories
    )


# =========================================================
# ADMIN - ADD CATEGORY
# =========================================================

@app.route(
    "/admin/categories/add",
    methods=["POST"]
)
@admin_required
def admin_add_category():

    name = request.form.get(
        "name",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    icon = request.form.get(
        "icon",
        "📦"
    ).strip()

    if not name:

        flash(
            "Category name is required.",
            "error"
        )

        return redirect(
            url_for("admin_categories")
        )

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO categories
            (
                name,
                description,
                icon
            )
            VALUES (?, ?, ?)
        """, (
            name,
            description,
            icon
        ))

        conn.commit()

        flash(
            "Category added successfully.",
            "success"
        )

    except Exception:

        flash(
            "Category already exists or could not be added.",
            "error"
        )

    finally:

        conn.close()

    return redirect(
        url_for("admin_categories")
    )


# =========================================================
# ADMIN - USERS
# =========================================================

@app.route("/admin/users")
@admin_required
def admin_users():

    conn = get_db()

    users = conn.execute("""
        SELECT *
        FROM users
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/users.html",
        users=users
    )


# =========================================================
# ADMIN - ORDERS
# =========================================================

@app.route("/admin/orders")
@admin_required
def admin_orders():

    conn = get_db()

    orders = conn.execute("""
        SELECT
            orders.*,
            users.username,
            users.email

        FROM orders

        JOIN users
            ON users.id = orders.user_id

        ORDER BY orders.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/orders.html",
        orders=orders
    )


# =========================================================
# ADMIN - PAYMENTS
# =========================================================

@app.route("/admin/payments")
@admin_required
def admin_payments():

    conn = get_db()

    payments = conn.execute("""
        SELECT
            payments.*,
            users.username,
            users.email

        FROM payments

        LEFT JOIN users
            ON users.id = payments.user_id

        ORDER BY payments.id DESC
    """).fetchall()

    conn.close()

    return render_template(
        "admin/payments.html",
        payments=payments
    )


# =========================================================
# ADMIN - USER STATUS
# =========================================================

@app.route(
    "/admin/users/<int:user_id>/toggle",
    methods=["POST"]
)
@admin_required
def admin_toggle_user(user_id):

    conn = get_db()

    user = conn.execute("""
        SELECT is_active
        FROM users
        WHERE id = ?
    """, (user_id,)).fetchone()

    if user:

        new_status = 0 if user["is_active"] else 1

        conn.execute("""
            UPDATE users
            SET is_active = ?
            WHERE id = ?
        """, (
            new_status,
            user_id
        ))

        conn.commit()

        flash(
            "User status updated.",
            "success"
        )

    conn.close()

    return redirect(
        url_for("admin_users")
    )

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=True
    )