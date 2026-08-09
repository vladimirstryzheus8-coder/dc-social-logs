# =========================================================
# DC SOCIAL LOGS 🪵
# DATABASE
# =========================================================

import sqlite3
from datetime import datetime

DATABASE = "dcsociallogs.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_tables():
    conn = get_db()
    cursor = conn.cursor()

    # =====================================================
    # USERS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            wallet_balance REAL DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =====================================================
    # CATEGORIES
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            icon TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =====================================================
    # PRODUCTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            category_id INTEGER NOT NULL,

            name TEXT NOT NULL,
            description TEXT,

            price REAL DEFAULT 0,
            old_price REAL DEFAULT 0,

            image TEXT,

            delivery_type TEXT DEFAULT 'automatic',
            delivery_information TEXT,

            featured INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (category_id)
                REFERENCES categories(id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # STOCK
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id INTEGER NOT NULL,

            stock_content TEXT NOT NULL,

            status TEXT DEFAULT 'available',

            sold_to_user_id INTEGER,
            order_id INTEGER,

            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            sold_at TEXT,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE,

            FOREIGN KEY (sold_to_user_id)
                REFERENCES users(id)
                ON DELETE SET NULL
        )
    """)

    # =====================================================
    # ORDERS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            order_number TEXT UNIQUE NOT NULL,

            total_amount REAL DEFAULT 0,

            status TEXT DEFAULT 'pending',

            payment_status TEXT DEFAULT 'pending',

            delivery_status TEXT DEFAULT 'pending',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # ORDER ITEMS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,

            product_name TEXT NOT NULL,

            quantity INTEGER DEFAULT 1,

            price REAL DEFAULT 0,
            subtotal REAL DEFAULT 0,

            FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE CASCADE,

            FOREIGN KEY (product_id)
                REFERENCES products(id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # TRANSACTIONS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,

            transaction_type TEXT NOT NULL,

            amount REAL DEFAULT 0,

            reference TEXT UNIQUE,

            description TEXT,

            status TEXT DEFAULT 'pending',

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # PAYMENTS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            order_id INTEGER,

            reference TEXT UNIQUE NOT NULL,

            amount REAL DEFAULT 0,

            gateway TEXT,

            gateway_transaction_id TEXT,

            status TEXT DEFAULT 'pending',

            payment_data TEXT,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE SET NULL,

            FOREIGN KEY (order_id)
                REFERENCES orders(id)
                ON DELETE SET NULL
        )
    """)

    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            title TEXT NOT NULL,
            message TEXT NOT NULL,

            notification_type TEXT DEFAULT 'info',

            is_read INTEGER DEFAULT 0,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    # =====================================================
    # SUPPORT SETTINGS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS support_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            telegram TEXT,
            whatsapp TEXT,
            email TEXT,

            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =====================================================
    # WEBSITE SETTINGS
    # =====================================================

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,

            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =====================================================
    # DEFAULT CATEGORIES
    # =====================================================

    categories = [
        (
            "Social Media Accounts",
            "Social media account products",
            "📱"
        ),
        (
            "Texting Apps",
            "Texting and communication applications",
            "💬"
        ),
        (
            "Streaming Apps",
            "Streaming and entertainment services",
            "🎬"
        ),
        (
            "Premium VPNs",
            "Premium VPN products",
            "🔐"
        ),
        (
            "Dating Apps",
            "Dating application products",
            "❤️"
        ),
        (
            "9Proxy",
            "9Proxy products and services",
            "🌐"
        )
    ]

    for name, description, icon in categories:
        cursor.execute("""
            INSERT OR IGNORE INTO categories
            (name, description, icon)
            VALUES (?, ?, ?)
        """, (name, description, icon))

    # =====================================================
    # SUPPORT INFORMATION
    # =====================================================

    cursor.execute("""
        SELECT COUNT(*) FROM support_settings
    """)

    support_exists = cursor.fetchone()[0]

    if support_exists == 0:
        cursor.execute("""
            INSERT INTO support_settings
            (telegram, whatsapp, email)
            VALUES (?, ?, ?)
        """, (
            "https://t.me/Official_Dcsociallogs",
            "https://wa.me/2349016685135",
            "dcsociallogs1@gmail.com"
        ))

    # =====================================================
    # SITE SETTINGS
    # =====================================================

    default_settings = [
        ("site_name", "DC SOCIAL LOGS"),
        (
            "tagline",
            "Your Digital World, Delivered Instantly."
        ),
        (
            "description",
            "Discover premium digital products, services, and subscriptions — all in one place."
        ),
        ("currency", "₦"),
        ("max_stock_per_product", "200")
    ]

    for key, value in default_settings:
        cursor.execute("""
            INSERT OR IGNORE INTO site_settings
            (setting_key, setting_value)
            VALUES (?, ?)
        """, (key, value))

    conn.commit()
    conn.close()


# =========================================================
# PRODUCT STOCK FUNCTIONS
# =========================================================

def add_stock(product_id, stock_items):
    """
    Add multiple stock items to a product.

    Example:

    add_stock(
        1,
        [
            "account1@email.com:password123",
            "account2@email.com:password456"
        ]
    )
    """

    conn = get_db()
    cursor = conn.cursor()

    for item in stock_items:

        item = str(item).strip()

        if not item:
            continue

        cursor.execute("""
            INSERT INTO stock
            (product_id, stock_content)
            VALUES (?, ?)
        """, (product_id, item))

    conn.commit()
    conn.close()


def get_available_stock(product_id):
    conn = get_db()

    stock = conn.execute("""
        SELECT *
        FROM stock
        WHERE product_id = ?
        AND status = 'available'
        ORDER BY id ASC
    """, (product_id,)).fetchall()

    conn.close()

    return stock


def get_stock_count(product_id):
    conn = get_db()

    count = conn.execute("""
        SELECT COUNT(*)
        FROM stock
        WHERE product_id = ?
        AND status = 'available'
    """, (product_id,)).fetchone()[0]

    conn.close()

    return count


# =========================================================
# GET ONE STOCK ITEM
# =========================================================

def get_next_stock(product_id):
    conn = get_db()

    stock = conn.execute("""
        SELECT *
        FROM stock
        WHERE product_id = ?
        AND status = 'available'
        ORDER BY id ASC
        LIMIT 1
    """, (product_id,)).fetchone()

    conn.close()

    return stock


# =========================================================
# MARK STOCK AS SOLD
# =========================================================

def mark_stock_sold(stock_id, user_id=None, order_id=None):

    conn = get_db()

    conn.execute("""
        UPDATE stock
        SET
            status = 'sold',
            sold_to_user_id = ?,
            order_id = ?,
            sold_at = ?
        WHERE id = ?
        AND status = 'available'
    """, (
        user_id,
        order_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        stock_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# CREATE ADMIN USER
# =========================================================

def create_admin(username, email, password):

    conn = get_db()

    try:

        conn.execute("""
            INSERT INTO users
            (
                username,
                email,
                password,
                is_admin
            )
            VALUES (?, ?, ?, 1)
        """, (
            username,
            email,
            password
        ))

        conn.commit()

        return True

    except sqlite3.IntegrityError:

        return False

    finally:

        conn.close()


# =========================================================
# INITIALIZE DATABASE
# =========================================================

if __name__ == "__main__":

    create_tables()

    print("====================================")
    print(" DC SOCIAL LOGS DATABASE")
    print("====================================")
    print("Database created successfully.")
    print("Categories created successfully.")
    print("Support information configured.")
    print("Ready for products and stock.")
    print("====================================")