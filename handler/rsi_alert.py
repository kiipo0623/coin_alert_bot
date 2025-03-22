from telegram.ext import ContextTypes
from util.binance import get_ohlcv
import pandas as pd
import ta

async def check_rsi(context: ContextTypes.DEFAULT_TYPE):
    df = get_ohlcv("BTC/USDT")
    rsi = ta.momentum.RSIIndicator(df["close"]).rsi().iloc[-1]
    if rsi < 30:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f"🧘 RSI is low: {rsi:.2f}")
