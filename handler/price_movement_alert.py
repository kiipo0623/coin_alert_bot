from telegram.ext import ContextTypes
from util.binance import get_price, get_ohlcv, get_top_volume_symbols
import datetime

ALERT_LOG = {}  # {symbol: last_alert_level}
VOLUME_THRESHOLD = 500_000_000 
START_THRESHOLD = 0.005
SYMBOL_CACHE = [] 

def get_open_price(symbol: str):
    df = get_ohlcv(symbol, timeframe="1h", limit=24)
    today = datetime.datetime.now(datetime.timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    for i in range(len(df)):
        ts = datetime.datetime.fromtimestamp(df.index[i] / 1000, tz=datetime.timezone.utc)
        if ts >= today:
            return df.iloc[i]["open"]
    return df.iloc[-1]["open"]

async def check_price_deviation(context: ContextTypes.DEFAULT_TYPE):
    global SYMBOL_CACHE

    all_symbols = get_top_volume_symbols()
    top_symbols = []

    for symbol in all_symbols:
        df = get_ohlcv(symbol, timeframe="1h", limit=1)
        if df is None or df.empty:
            continue
        volume = df.iloc[-1]["quoteVolume"] if "quoteVolume" in df.columns else 0
        if volume >= VOLUME_THRESHOLD:
            top_symbols.append(symbol)

    messages = []

    for symbol in top_symbols:
        try:
            open_price = get_open_price(symbol)
            current_price = get_price(symbol)

            deviation = abs(current_price - open_price) / open_price
            level = 0
            threshold = START_THRESHOLD

            while deviation >= threshold:
                level += 1
                threshold *= 2
                
            if level == 0 or ALERT_LOG.get(symbol, -1) >= level:
                continue

            ALERT_LOG[symbol] = level

            direction = "📈 UP" if current_price > open_price else "📉 DOWN"
            messages.append(
                f"{direction} {symbol} price moved {deviation*100:.2f}% from daily open\n"
                f"Open: ${open_price:.2f} → Now: ${current_price:.2f}"
            )

        except Exception as e:
            print(f"[WARN] {symbol} price deviation error: {e}")

    if messages:
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="\n\n".join(messages)
        )