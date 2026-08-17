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

XAU_SYMBOL = "XAU/USD"

# Analysis settings
INTERVAL = "15min"
OUTPUT_SIZE = 100

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
    return "King of XAU_NAS Gold Bot is running!"


@web_app.route("/health")
def health():
    return "OK"


def run_web_server():
    web_app.run(
        host="0.0.0.0",
        port=PORT
    )


# =========================
# TWELVE DATA REQUEST
# =========================

def twelve_data_request(endpoint, params):

    if not TWELVE_DATA_API_KEY:
        return None, "Twelve Data API key is missing."

    params["apikey"] = TWELVE_DATA_API_KEY

    url = f"https://api.twelvedata.com/{endpoint}"

    try:
        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        if "status" in data and data["status"] == "error":
            return None, data.get(
                "message",
                "Twelve Data returned an error."
            )

        if "code" in data and "message" in data:
            return None, data["message"]

        return data, None

    except requests.RequestException as error:

        logger.error(
            "Twelve Data connection error: %s",
            error
        )

        return None, "Unable to connect to Twelve Data."

    except Exception as error:

        logger.error(
            "Unexpected API error: %s",
            error
        )

        return None, "Unexpected market-data error."


# =========================
# LIVE PRICE
# =========================

def get_price(symbol=XAU_SYMBOL):

    data, error = twelve_data_request(
        "price",
        {
            "symbol": symbol
        }
    )

    if error:
        return None, error

    try:

        if "price" not in data:
            return None, "No price returned by Twelve Data."

        return float(data["price"]), None

    except Exception:

        return None, "Invalid price received."


# =========================
# TIME SERIES
# =========================

def get_candles():

    data, error = twelve_data_request(
        "time_series",
        {
            "symbol": XAU_SYMBOL,
            "interval": INTERVAL,
            "outputsize": OUTPUT_SIZE,
            "format": "JSON"
        }
    )

    if error:
        return None, error

    try:

        values = data.get("values")

        if not values:
            return None, "No candle data returned."

        candles = []

        for candle in reversed(values):

            candles.append({
                "open": float(candle["open"]),
                "high": float(candle["high"]),
                "low": float(candle["low"]),
                "close": float(candle["close"]),
            })

        return candles, None

    except Exception as error:

        logger.error(
            "Candle parsing error: %s",
            error
        )

        return None, "Unable to process candle data."


# =========================
# EMA
# =========================

def calculate_ema(values, period):

    if len(values) < period:
        return None

    multiplier = 2 / (period + 1)

    ema = sum(values[:period]) / period

    for price in values[period:]:

        ema = (
            (price - ema) * multiplier
        ) + ema

    return ema


# =========================
# RSI
# =========================

def calculate_rsi(values, period=14):

    if len(values) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(1, len(values)):

        change = values[i] - values[i - 1]

        if change > 0:

            gains.append(change)
            losses.append(0)

        else:

            gains.append(0)
            losses.append(abs(change))

    average_gain = sum(
        gains[:period]
    ) / period

    average_loss = sum(
        losses[:period]
    ) / period

    for i in range(period, len(gains)):

        average_gain = (
            (average_gain * (period - 1))
            + gains[i]
        ) / period

        average_loss = (
            (average_loss * (period - 1))
            + losses[i]
        ) / period

    if average_loss == 0:
        return 100.0

    rs = average_gain / average_loss

    return 100 - (100 / (1 + rs))


# =========================
# ATR
# =========================

def calculate_atr(candles, period=14):

    if len(candles) < period + 1:
        return None

    true_ranges = []

    for i in range(1, len(candles)):

        high = candles[i]["high"]
        low = candles[i]["low"]
        previous_close = candles[i - 1]["close"]

        true_range = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )

        true_ranges.append(true_range)

    if len(true_ranges) < period:
        return None

    atr = sum(
        true_ranges[:period]
    ) / period

    for value in true_ranges[period:]:

        atr = (
            ((atr * (period - 1)) + value)
            / period
        )

    return atr


# =========================
# GOLD ANALYSIS ENGINE
# =========================

def analyze_gold():

    candles, error = get_candles()

    if error:
        return None, error

    if len(candles) < 50:
        return None, "Not enough candle data for analysis."

    closes = [
        candle["close"]
        for candle in candles
    ]

    current_price = closes[-1]

    ema20 = calculate_ema(
        closes,
        20
    )

    ema50 = calculate_ema(
        closes,
        50
    )

    rsi = calculate_rsi(
        closes,
        14
    )

    atr = calculate_atr(
        candles,
        14
    )

    if any(
        value is None
        for value in [ema20, ema50, rsi, atr]
    ):
        return None, "Technical indicators could not be calculated."

    # =========================
    # SIGNAL SCORE
    # =========================

    score = 0

    # Trend
    if current_price > ema20:
        score += 1
    else:
        score -= 1

    if ema20 > ema50:
        score += 2
    else:
        score -= 2

    # RSI
    if 50 <= rsi <= 70:
        score += 1

    elif 30 <= rsi < 50:
        score -= 1

    elif rsi > 70:
        score -= 1

    elif rsi < 30:
        score += 1

    # =========================
    # SIGNAL
    # =========================

    if score >= 3:

        signal = "BUY"
        signal_icon = "🟢"

    elif score <= -3:

        signal = "SELL"
        signal_icon = "🔴"

    else:

        signal = "WAIT"
        signal_icon = "🟡"

    # =========================
    # TREND
    # =========================

    if current_price > ema20 and ema20 > ema50:

        trend = "BULLISH 📈"

    elif current_price < ema20 and ema20 < ema50:

        trend = "BEARISH 📉"

    else:

        trend = "MIXED ↔️"

    # =========================
    # ENTRY / SL / TP
    # =========================

    entry = current_price

    if signal == "BUY":

        stop_loss = entry - (atr * 1.5)

        take_profit_1 = entry + (atr * 1.5)

        take_profit_2 = entry + (atr * 3.0)

    elif signal == "SELL":

        stop_loss = entry + (atr * 1.5)

        take_profit_1 = entry - (atr * 1.5)

        take_profit_2 = entry - (atr * 3.0)

    else:

        stop_loss = None
        take_profit_1 = None
        take_profit_2 = None

    # =========================
    # CONFIDENCE
    # =========================

    confidence = min(
        95,
        max(
            50,
            50 + abs(score) * 10
        )
    )

    result = {
        "price": current_price,
        "ema20": ema20,
        "ema50": ema50,
        "rsi": rsi,
        "atr": atr,
        "trend": trend,
        "signal": signal,
        "signal_icon": signal_icon,
        "confidence": confidence,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit_1": take_profit_1,
        "take_profit_2": take_profit_2,
        "score": score,
    }

    return result, None


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
                "🟡 GOLD ANALYSIS",
                callback_data="gold"
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

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    message = (
        "👑 *KING OF XAU_NAS* 👑\n\n"
        "Welcome to your Gold trading assistant.\n\n"
        "🟡 *XAU/USD — GOLD*\n\n"
        "📡 Live market data\n"
        "📈 Technical analysis\n"
        "🎯 Entry / SL / TP\n"
        "💪 Signal confidence\n\n"
        "Choose an option below:"
    )

    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# =========================
# GOLD COMMAND
# =========================

async def gold_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "🔎 Analyzing XAU/USD...\n"
        "Please wait..."
    )

    result, error = analyze_gold()

    if error:

        await update.message.reply_text(
            "❌ *GOLD ANALYSIS ERROR*\n\n"
            f"{error}",
            parse_mode="Markdown"
        )

        return

    message = format_gold_analysis(
        result
    )

    await update.message.reply_text(
        message,
        parse_mode="Markdown"
    )


# =========================
# FORMAT ANALYSIS
# =========================

def format_gold_analysis(result):

    price = result["price"]
    ema20 = result["ema20"]
    ema50 = result["ema50"]
    rsi = result["rsi"]
    atr = result["atr"]

    signal = result["signal"]
    signal_icon = result["signal_icon"]
    confidence = result["confidence"]

    entry = result["entry"]
    stop_loss = result["stop_loss"]
    tp1 = result["take_profit_1"]
    tp2 = result["take_profit_2"]

    trend = result["trend"]

    message = (
        "👑 *KING OF XAU_NAS — GOLD*\n\n"
        "🟡 *XAU/USD*\n\n"
        f"💰 Price: `${price:,.2f}`\n"
        f"📈 Trend: *{trend}*\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📊 *TECHNICAL DATA*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"EMA 20: `{ema20:,.2f}`\n"
        f"EMA 50: `{ema50:,.2f}`\n"
        f"RSI 14: `{rsi:.1f}`\n"
        f"ATR 14: `{atr:.2f}`\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🎯 *TRADE ANALYSIS*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{signal_icon} Signal: *{signal}*\n"
        f"💪 Confidence: *{confidence}%*\n"
    )

    if signal != "WAIT":

        message += (
            "\n"
            f"🎯 Entry: `${entry:,.2f}`\n"
            f"🛑 Stop Loss: `${stop_loss:,.2f}`\n"
            f"🎯 Take Profit 1: `${tp1:,.2f}`\n"
            f"🎯 Take Profit 2: `${tp2:,.2f}`\n"
        )

    else:

        message += (
            "\n"
            "⏳ No clear setup at the moment.\n"
            "Wait for stronger confirmation.\n"
        )

    message += (
        "\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"⏱️ Timeframe: *{INTERVAL}*\n"
        "📡 Data: Twelve Data\n\n"
        "⚠️ *Analysis only — not financial advice.*\n"
        "⚠️ No signal guarantees a profitable trade."
    )

    return message


# =========================
# HELP
# =========================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    message = (
        "ℹ️ *KING OF XAU_NAS — GOLD HELP*\n\n"
        "/start — Open the main menu\n"
        "/gold — Analyze XAU/USD\n"
        "/status — Check bot status\n"
        "/help — Show help\n\n"
        "📊 The Gold scanner uses live Twelve Data "
        "market information and technical indicators.\n\n"
        "Indicators:\n"
        "• EMA 20\n"
        "• EMA 50\n"
        "• RSI 14\n"
        "• ATR 14\n\n"
        "Signals:\n"
        "🟢 BUY\n"
        "🔴 SELL\n"
        "🟡 WAIT\n\n"
        "⚠️ Trading involves risk."
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

    price, error = get_price()

    if price is not None:

        price_text = f"${price:,.2f}"

        data_status = "🟢 ONLINE"

    else:

        price_text = "Unavailable"

        data_status = "🔴 OFFLINE"

    message = (
        "👑 *KING OF XAU_NAS STATUS*\n\n"
        "🟢 Telegram Bot: ONLINE\n"
        f"🟡 XAU/USD: {price_text}\n"
        f"📡 Twelve Data: {data_status}\n"
        "📊 Gold Scanner: READY\n\n"
        "Nasdaq: DISABLED"
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

    # =========================
    # GOLD
    # =========================

    if query.data == "gold":

        await query.edit_message_text(
            "🔎 *Analyzing XAU/USD...*\n\n"
            "Please wait...",
            parse_mode="Markdown"
        )

        result, error = analyze_gold()

        if error:

            message = (
                "❌ *GOLD ANALYSIS ERROR*\n\n"
                f"{error}"
            )

        else:

            message = format_gold_analysis(
                result
            )

        await query.edit_message_text(
            message,
            parse_mode="Markdown"
        )

    # =========================
    # STATUS
    # =========================

    elif query.data == "status":

        price, error = get_price()

        if price is not None:

            price_text = f"${price:,.2f}"

            data_status = "🟢 ONLINE"

        else:

            price_text = "Unavailable"

            data_status = "🔴 OFFLINE"

        message = (
            "📊 *MARKET STATUS*\n\n"
            "🟢 Telegram Bot: ONLINE\n"
            f"🟡 XAU/USD: {price_text}\n"
            f"📡 Twelve Data: {data_status}\n"
            "📊 Gold Scanner: READY\n\n"
            "Nasdaq: DISABLED"
        )

        await query.edit_message_text(
            message,
            parse_mode="Markdown"
        )

    # =========================
    # HELP
    # =========================

    elif query.data == "help":

        message = (
            "ℹ️ *KING OF XAU_NAS — GOLD*\n\n"
            "This bot is focused on XAU/USD Gold.\n\n"
            "✅ Telegram connection\n"
            "✅ Live XAU/USD price\n"
            "✅ EMA trend analysis\n"
            "✅ RSI analysis\n"
            "✅ ATR volatility analysis\n"
            "✅ BUY / SELL / WAIT\n"
            "✅ Entry calculation\n"
            "✅ Stop Loss calculation\n"
            "✅ Take Profit calculation\n\n"
            "⚠️ Analysis only. Trading involves risk."
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

    # =========================
    # START WEB SERVER
    # =========================

    Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # =========================
    # TELEGRAM APPLICATION
    # =========================

    application = (
        Application
        .builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    # =========================
    # COMMANDS
    # =========================

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "gold",
            gold_command
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status_command
        )
    )

    # =========================
    # BUTTONS
    # =========================

    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    logger.info(
        "King of XAU_NAS Gold Bot started!"
    )

    # =========================
    # START POLLING
    # =========================

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


# =========================
# RUN
# =========================

if __name__ == "__main__":
    main()
