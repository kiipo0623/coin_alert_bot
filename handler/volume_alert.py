# ============================
# handlers/volume_alert.py
# ============================
from telegram.ext import ContextTypes
from util.binance import get_ohlcv, get_top_volume_symbols

TIMEFRAME = "5m"
VOLUME_SPIKE_RATIO = 2

async def check_volume_spike(context: ContextTypes.DEFAULT_TYPE):
    symbols = get_top_volume_symbols()

    for symbol in symbols:
        try:
            df = get_ohlcv(symbol, timeframe=TIMEFRAME, limit=3)
            prev_volume = df.iloc[-2]["volume"]
            current_volume = df.iloc[-1]["volume"]

            if prev_volume == 0:
                continue  # 0으로 나누기 방지

            ratio = current_volume / prev_volume

            if ratio >= VOLUME_SPIKE_RATIO:
                await context.bot.send_message(
                    chat_id=context.job.chat_id,
                    text=(
                        f"📊 {symbol} volume spike!\n"
                        f"5-min volume increased {ratio:.1f}x\n"
                        f"Prev: {prev_volume:.2f}, Now: {current_volume:.2f}"
                    )
                )

        except Exception as e:
            # 심볼별 오류가 전체 감시를 막지 않도록 pass
            print(f"[WARN] {symbol} error: {e}")
