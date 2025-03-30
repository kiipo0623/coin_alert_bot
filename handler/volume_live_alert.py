import asyncio
import datetime
import json
import websockets
from telegram import Bot
from util.binance import get_top_volume_symbols

BOT_TOKEN = None
CHAT_ID = None

LIVE_VOLUME_RATIO = 3
LIVE_ALERT_COOLTIME_MINUTES = 3
LIVE_ALERT_LOG = {}
VOLUME_TRACKER = {}

UPDATE_INTERVAL = 600
error_notified = False

def build_stream_url(symbols):
    stream_names = [f"{s}@kline_1m" for s in symbols]
    joined = "/".join(stream_names)
    return f"wss://fstream.binance.com/stream?streams={joined}"


async def handle_message(bot, data):
    stream = data.get("stream", "")
    payload = data.get("data", {})
    k = payload.get("k", {})

    symbol = stream.split("@")[0]
    open_time = k["t"]
    open_price = float(k["o"])
    current_price = float(k["c"])
    curr_volume = float(k["v"])

    emoji = "❤️" if current_price >= open_price else "💚"

    # 새로운 캔들 시작
    if symbol not in VOLUME_TRACKER or VOLUME_TRACKER[symbol]["open_time"] != open_time:
        VOLUME_TRACKER[symbol] = {
            "open_time": open_time,
            "start_volume": curr_volume,
            "curr_volume": curr_volume,
        }
        return

    prev_volume = VOLUME_TRACKER[symbol]["start_volume"]
    now = datetime.datetime.utcnow()
    last_alert_time = LIVE_ALERT_LOG.get(symbol)
    minutes_since = (now - last_alert_time).total_seconds() / 60 if last_alert_time else None

    ratio = curr_volume / prev_volume if prev_volume > 0 else 0
    price_change_pct = ((current_price - open_price) / open_price) * 100
    price_change_line = f"{current_price:.0f} ({price_change_pct:+.1f}%) from 1m open"

    if (
        ratio >= LIVE_VOLUME_RATIO
        and (last_alert_time is None or minutes_since >= LIVE_ALERT_COOLTIME_MINUTES)
    ):
        LIVE_ALERT_LOG[symbol] = now
        await bot.send_message(
            chat_id=CHAT_ID,
            text=(
                f"{emoji} {symbol.upper()} LIVE volume spike!\n"
                f"Volume {ratio:.1f}x in current 1m\n"
                f"{price_change_line}"
            ),
        )


async def connect_and_listen(bot, symbols):
    global error_notified
    url = build_stream_url(symbols)

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=10) as ws:
                print(f"[INFO] WebSocket connected for symbols: {symbols}")
                error_notified = False
                async for message in ws:
                    data = json.loads(message)
                    await handle_message(bot, data)

        except Exception as e:
            print(f"[WARN] WebSocket error: {e}")
            if not error_notified:
                try:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"⚠️ [WebSocket Error]\n{type(e).__name__}: {e}",
                    )
                    error_notified = True
                except Exception as te:
                    print(f"[ERROR] Failed to send Telegram error message: {te}")
            await asyncio.sleep(5)
            break  # 재연결 루프로 나가기


async def start_volume_ws_alert(token, chat_id):
    global BOT_TOKEN, CHAT_ID
    BOT_TOKEN = token
    CHAT_ID = chat_id
    bot = Bot(token=token)

    while True:
        try:
            symbols = get_top_volume_symbols()
            await connect_and_listen(bot, symbols)
            await asyncio.sleep(UPDATE_INTERVAL)
        except Exception as e:
            print(f"[ERROR] Main WS loop error: {e}")
            if not error_notified:
                try:
                    await bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"⚠️ [Main Loop Error]\n{type(e).__name__}: {e}",
                    )
                    error_notified = True
                except Exception as te:
                    print(f"[ERROR] Failed to send main loop error message: {te}")
            await asyncio.sleep(10)
