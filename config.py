import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    # =========================
    # FLASK
    # =========================

    SECRET_KEY = os.getenv(
        "SESSION_SECRET",
        "change-this-secret-key-in-production"
    )

    # =========================
    # DATABASE
    # =========================

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///dc_social_logs.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =========================
    # SESSION SECURITY
    # =========================

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Set to True when your production website
    # is running with HTTPS.
    SESSION_COOKIE_SECURE = os.getenv(
        "SESSION_COOKIE_SECURE",
        "False"
    ).lower() == "true"

    # =========================
    # WEBSITE
    # =========================

    WEBSITE_NAME = "DC SOCIAL LOGS 🪵"

    WEBSITE_TAGLINE = (
        "Your Digital World, Delivered Instantly."
    )

    WEBSITE_DESCRIPTION = (
        "Discover premium digital products, services, "
        "and subscriptions — all in one place."
    )

    CURRENCY = "NGN"

    CURRENCY_SYMBOL = "₦"

    # =========================
    # BULK DISCOUNT
    # =========================

    # Default rule:
    # 1–5 units = 5% discount

    BULK_MIN_QUANTITY = int(
        os.getenv(
            "BULK_MIN_QUANTITY",
            "1"
        )
    )

    BULK_MAX_QUANTITY = int(
        os.getenv(
            "BULK_MAX_QUANTITY",
            "5"
        )
    )

    BULK_DISCOUNT_PERCENT = float(
        os.getenv(
            "BULK_DISCOUNT_PERCENT",
            "5"
        )
    )

    # =========================
    # MAXIMUM INVENTORY
    # =========================

    MAX_PRODUCT_STOCK = int(
        os.getenv(
            "MAX_PRODUCT_STOCK",
            "200"
        )
    )

    # =========================
    # KORAPAY
    # =========================

    KORAPAY_PUBLIC_KEY = os.getenv(
        "KORAPAY_PUBLIC_KEY",
        ""
    )

    KORAPAY_SECRET_KEY = os.getenv(
        "KORAPAY_SECRET_KEY",
        ""
    )

    KORAPAY_WEBHOOK_SECRET = os.getenv(
        "KORAPAY_WEBHOOK_SECRET",
        ""
    )

    # =========================
    # REFERRAL SYSTEM
    # =========================

    REFERRAL_ENABLED = (
        os.getenv(
            "REFERRAL_ENABLED",
            "True"
        ).lower()
        == "true"
    )

    REFERRAL_REWARD_PERCENT = float(
        os.getenv(
            "REFERRAL_REWARD_PERCENT",
            "3"
        )
    )

 # =========================
# SUPPORT
# =========================

SUPPORT_EMAIL = os.getenv(
    "SUPPORT_EMAIL",
    "dcsociallogs1@gmail.com"
)

WHATSAPP_SUPPORT = os.getenv(
    "WHATSAPP_SUPPORT",
    "https://wa.me/2349016685135"
)

TELEGRAM_SUPPORT = os.getenv(
    "TELEGRAM_SUPPORT",
    "https://t.me/Official_Dcsociallogs"
)