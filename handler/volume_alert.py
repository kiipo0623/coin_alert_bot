from telegram.ext import ContextTypes
from util.binance import get_ohlcv, get_top_volume_symbols

async def detect_volume_spike(
    context: ContextTypes.DEFAULT_TYPE,
    timeframe: str,
    volume_ratio_threshold: float,
    label: str
):
    symbols = get_top_volume_symbols()

    for symbol in symbols:
        try:
            df = get_ohlcv(symbol, timeframe=timeframe, limit=3)
            prev_volume = df.iloc[-2]["volume"]
            current_volume = df.iloc[-1]["volume"]

            if prev_volume == 0:
                continue

            ratio = current_volume / prev_volume

            if ratio >= volume_ratio_threshold:
                await context.bot.send_message(
                    chat_id=context.job.chat_id,
                    text=(
                        f"📊 {symbol} volume spike ({label})\n"
                        f"{timeframe} volume increased {ratio:.1f}x\n"
                        f"Prev: {prev_volume:.2f}, Now: {current_volume:.2f}"
                    )
                )

        except Exception as e:
            print(f"[WARN] {symbol} error in {label}: {e}")

async def check_volume_spike_5m(context: ContextTypes.DEFAULT_TYPE):
    await detect_volume_spike(
        context=context,
        timeframe="5m",
        volume_ratio_threshold=2,
        label="5m / x2"
    )

async def check_volume_spike_1m(context: ContextTypes.DEFAULT_TYPE):
    await detect_volume_spike(
        context=context,
        timeframe="1m",
        volume_ratio_threshold=3,
        label="1m / x3"
    )
