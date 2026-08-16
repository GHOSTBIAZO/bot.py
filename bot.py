import os
import logging
from flask import Flask
from threading import Thread

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

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

# =========================
# LOGGING
# =========================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# =========================
# WEB SERVER FOR RENDER
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "King of XAU_NAS Bot is running!"


@app.route("/health")
def health():
    return "OK"


def run_web_server():
    app.run(host="0.0.0.0", port=PORT)


# =========================
# TELEGRAM COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton("🟡 XAUUSD GOLD", callback_data="xauusd")
        ],
        [
            InlineKeyboardButton("🔵 NAS100", callback_data="nas100")
        ],
        [
            InlineKeyboardButton("📊 MARKET STATUS", callback_data="status")
        ],
        [
            InlineKeyboardButton("ℹ️ HELP", callback_data="help")
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
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "👑 *KING OF XAU_NAS — HELP*\n\n"
        "/start — Open the main menu\n"
        "/help — Show this help menu\n"
        "/status — Check bot status\n\n"
        "📊 More features will be added next."
    )

    await update.message.reply_text(
        message,
        parse_mode="Markdown",
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🟢 *BOT STATUS*\n\n"
        "King of XAU_NAS is online.\n"
        "Market scanner: 🔧 Being built\n"
        "XAUUSD scanner: 🔧 Being built\n"
        "NAS100 scanner: 🔧 Being built",
        parse_mode="Markdown",
    )


# =========================
# BUTTON HANDLER
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    if query.data == "xauusd":

        await query.edit_message_text(
            "🟡 *XAUUSD GOLD*\n\n"
            "Scanner is being prepared.\n\n"
            "Next we will add:\n"
            "• Live price\n"
            "• Market direction\n"
            "• Entry\n"
            "• Stop Loss\n"
            "• Take Profit\n"
            "• Risk/Reward\n"
            "• AI analysis",
            parse_mode="Markdown",
        )

    elif query.data == "nas100":

        await query.edit_message_text(
            "🔵 *NAS100*\n\n"
            "Scanner is being prepared.\n\n"
            "Next we will add:\n"
            "• Live price\n"
            "• Market direction\n"
            "• Entry\n"
            "• Stop Loss\n"
            "• Take Profit\n"
            "• Risk/Reward\n"
            "• AI analysis",
            parse_mode="Markdown",
        )

    elif query.data == "status":

        await query.edit_message_text(
            "🟢 *KING OF XAU_NAS*\n\n"
            "Bot: ONLINE\n"
            "Telegram: CONNECTED\n"
            "Scanner: IN DEVELOPMENT\n\n"
            "We are building the trading engine next.",
            parse_mode="Markdown",
        )

    elif query.data == "help":

        await query.edit_message_text(
            "ℹ️ *KING OF XAU_NAS*\n\n"
            "This bot will scan XAUUSD and NAS100 "
            "and provide trading analysis.\n\n"
            "More features are coming next.",
            parse_mode="Markdown",
        )


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN environment variable is missing."
        )

    # Start Render web server
    Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # Create Telegram application
    application = Application.builder().token(TOKEN).build()

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

    print("👑 King of XAU_NAS Bot started!")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
