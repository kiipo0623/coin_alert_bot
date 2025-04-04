import logging
import asyncio
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from handler.price_alert import check_target_price, check_price_drop
from handler.rsi_alert import check_rsi
from handler.volume_alert import check_volume_spike_5m, check_volume_spike_1m
from handler.price_movement_alert import check_price_deviation
from command.price_ping import handle_price_command
from handler.volume_live_alert import check_volume_spike_3x

BOT_TOKEN = "7781510842:AAHU-Y8Nv6RXD7CakxoHIjWtD5YYARy8CQs"
CHAT_ID = 5875632146

logging.basicConfig(level=logging.INFO)

async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # JobQueue: periodic checks
    job_queue = app.job_queue
    job_queue.run_repeating(check_target_price, interval=60, chat_id=CHAT_ID)
    job_queue.run_repeating(check_price_drop, interval=60, chat_id=CHAT_ID)
    job_queue.run_repeating(check_rsi, interval=300, chat_id=CHAT_ID)
    job_queue.run_repeating(check_volume_spike_5m, interval=300, chat_id=CHAT_ID)
    job_queue.run_repeating(check_price_deviation, interval=60, chat_id=CHAT_ID)
    job_queue.run_repeating(check_volume_spike_1m, interval=60, chat_id=CHAT_ID)

    # WebSocket: live check
    asyncio.create_task(check_volume_spike_3x(BOT_TOKEN, CHAT_ID))

    app.add_handler(CommandHandler("price", handle_price_command))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    print("🤖 Bot is running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.run(start_bot())
