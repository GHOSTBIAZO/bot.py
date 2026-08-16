import os
import logging
from threading import Thread

import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================
# SETTINGS
# =========================

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY")
PORT = int(os.getenv("PORT", "10000"))

# Twelve Data symbols
XAU_SYMBOL = "XAU/USD"
NAS_SYMBOL = "NDX"

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# =========================
# WEB SERVER
# =========================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "King of XAU_NAS Bot is running!"


@web_app.route("/health")
def health():
    return "OK"


def run_web_server():
    web_app.run(
        host="0.0.0.0",
        port=PORT
    )


# =========================
# LIVE PRICE FUNCTION
# =========================

def get_price(symbol):

    if not TWELVE_DATA_API_KEY:
        return None, "Twelve Data API key is missing."

    url = "https://api.twelvedata.com/price"

    params = {
        "symbol": symbol,
        "apikey": TWELVE_DATA_API_KEY,
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        if "price" in data:

            return float(data["price"]), None

        if "message" in data:

            return None, data["message"]

        return None, "No price returned by the data provider."

    except Exception as error:

        logger.error("Price error: %s", error)

        return None, "Unable to connect to market data."


# =========================
# START COMMAND
# =========================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    keyboard = [

        [
            InlineKeyboardButton(
                "🟡 XAUUSD GOLD",
                callback_data="xauusd"
            )
        ],

        [
            InlineKeyboardButton(
                "🔵 NAS100",
                callback_data="nas100"
            )
        ],

        [
            InlineKeyboardButton(
                "📊 MARKET STATUS",
                callback_data="status"
            )
        ],

        [
            InlineKeyboardButton(
                "ℹ️ HELP",
                callback_data="help"
            )
        ],

    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "👑 *KING OF XAU_NAS*\n\n"
        "Welcome to your trading assistant.\n\n"
        "🟡 XAUUSD — Gold\n"
        "🔵 NAS100 — Nasdaq\n\n"
        "Choose a market below:"
    )

    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (
        "ℹ️ *KING OF XAU_NAS — HELP*\n\n"
        "/start — Open the main menu\n"
        "/help — Show help\n"
        "/status — Check bot status\n\n"
        "The live market-price system is now connected."
    )

    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )


# =========================
# STATUS
# =========================

async def status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    xau_price, xau_error = get_price(XAU_SYMBOL)
    nas_price, nas_error = get_price(NAS_SYMBOL)

    xau_status = (
        f"${xau_price:,.2f}"
        if xau_price is not None
        else "Unavailable"
    )

    nas_status = (
        f"{nas_price:,.2f}"
        if nas_price is not None
        else "Unavailable"
    )

    message = (
        "👑 *KING OF XAU_NAS STATUS*\n\n"
        "🟢 Telegram Bot: ONLINE\n"
        f"🟡 XAUUSD: {xau_status}\n"
        f"🔵 NAS100: {nas_status}\n\n"
        "📡 Live data connection: ACTIVE"
    )

    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    # -------------------------
    # XAUUSD
    # -------------------------

    if query.data == "xauusd":

        price, error = get_price(XAU_SYMBOL)

        if price is not None:

            message = (
                "🟡 *XAUUSD GOLD*\n\n"
                f"💰 Current price: `${price:,.2f}`\n\n"
                "📡 Live market data: ✅\n\n"
                "🔧 Technical scanner: NEXT STAGE\n"
                "🔧 Entry/SL/TP engine: NEXT STAGE\n"
                "🔧 AI analysis: NEXT STAGE"
            )

        else:

            message = (
                "🟡 *XAUUSD GOLD*\n\n"
                "❌ Live price unavailable.\n\n"
                f"Reason: {error}"
            )

        await query.edit_message_text(
            message,
            parse_mode="Markdown"
        )

    # -------------------------
    # NAS100
    # -------------------------

    elif query.data == "nas100":

        price, error = get_price(NAS_SYMBOL)

        if price is not None:

            message = (
                "🔵 *NAS100*\n\n"
                f"💰 Current price: `{price:,.2f}`\n\n"
                "📡 Live market data: ✅\n\n"
                "🔧 Technical scanner: NEXT STAGE\n"
                "🔧 Entry/SL/TP engine: NEXT STAGE\n"
                "🔧 AI analysis: NEXT STAGE"
            )

        else:

            message = (
                "🔵 *NAS100*\n\n"
                "❌ Live price unavailable.\n\n"
                f"Reason: {error}"
            )

        await query.edit_message_text(
            message,
            parse_mode="Markdown"
        )

    # -------------------------
    # STATUS
    # -------------------------

    elif query.data == "status":

        xau_price, _ = get_price(XAU_SYMBOL)
        nas_price, _ = get_price(NAS_SYMBOL)

        xau = (
            f"${xau_price:,.2f}"
            if xau_price is not None
            else "Unavailable"
        )

        nas = (
            f"{nas_price:,.2f}"
            if nas_price is not None
            else "Unavailable"
        )

        message = (
            "📊 *MARKET STATUS*\n\n"
            f"🟡 XAUUSD: {xau}\n"
            f"🔵 NAS100: {nas}\n\n"
            "📡 Data connection: ONLINE"
        )

        await query.edit_message_text(
            message,
            parse_mode="Markdown"
        )

    # -------------------------
    # HELP
    # -------------------------

    elif query.data == "help":

        message = (
            "ℹ️ *KING OF XAU_NAS*\n\n"
            "This bot is being built in stages.\n\n"
            "✅ Telegram connection\n"
            "✅ Live market-data connection\n"
            "🔧 Technical analysis\n"
            "🔧 BUY/SELL engine\n"
            "🔧 Entry + SL + TP\n"
            "🔧 Risk/Reward\n"
            "🔧 AI analysis"
        )

        await query.edit_message_text(
            message,
            parse_mode="Markdown"
        )


# =========================
# MAIN
# =========================

def main():

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is missing."
        )

    if not TWELVE_DATA_API_KEY:
        raise RuntimeError(
            "TWELVE_DATA_API_KEY is missing."
        )

    # Start web server for Render
    Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # Telegram application
    application = (
        Application
        .builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Commands
    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("status", status_command)
    )

    # Buttons
    application.add_handler(
        CallbackQueryHandler(button_handler)
    )

    logger.info(
        "King of XAU_NAS Bot started!"
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
