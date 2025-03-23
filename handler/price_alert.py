from telegram.ext import ContextTypes
from telegram import Bot
from util.binance import get_price, get_ohlcv
import datetime

TARGET_PRICES = sorted([30000, 35000, 40000, 45000, 50000, 55000, 60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000])
ALERT_STATE = {}
ALERT_INTERVAL_MINUTES = 30
DROP_PERCENT = 5

def get_open_price():
    today = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    df = get_ohlcv("BTC/USDT", timeframe="1h", limit=24)
    for i in range(len(df)):
        ts = datetime.datetime.fromtimestamp(df.index[i] / 1000, tz=datetime.timezone.utc)
        if ts >= today:
            return df.iloc[i]["open"]
    return df.iloc[-1]["open"]  # fallback

async def check_target_price(context: ContextTypes.DEFAULT_TYPE):
    price = get_price("BTC/USDT")
    now = datetime.datetime.now(datetime.timezone.utc)

    current_status = None
    target_to_alert = None

    for target in reversed(TARGET_PRICES):
        if price >= target:
            current_status = "above"
            target_to_alert = target
            break

    if current_status is None:
        for target in TARGET_PRICES:
            if price < target:
                current_status = "below"
                target_to_alert = target
                break

    if target_to_alert is None:
        return

    state = ALERT_STATE.get(target_to_alert, {})
    last_status = state.get("status")
    last_time = state.get("time")
    minutes_since = (now - last_time).total_seconds() / 60 if last_time else None

    if current_status != last_status and (last_time is None or minutes_since >= ALERT_INTERVAL_MINUTES):
        emoji = "📈" if current_status == "above" else "📉"
        verb = "rose above" if current_status == "above" else "fell below"

        ALERT_STATE[target_to_alert] = {"status": current_status, "time": now}

        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text=f"{emoji} BTC {verb} ${target_to_alert:,} (Current: ${price:,.2f})"
        )

async def check_price_drop(context: ContextTypes.DEFAULT_TYPE):
    price = get_price("BTC/USDT")
    base_price = get_open_price()
    drop = (base_price - price) / base_price * 100
    if drop >= DROP_PERCENT:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f"📉 BTC dropped {drop:.2f}% from daily open (${base_price:.2f} → ${price:.2f})")