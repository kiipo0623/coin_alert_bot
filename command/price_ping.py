from telegram import Update
from telegram.ext import ContextTypes
from util.binance import get_price

async def handle_price_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price = get_price("BTC/USDT")
    await update.message.reply_text(
        f"📈 BTC/USDT Current Price: ${price:,.2f}"
    )