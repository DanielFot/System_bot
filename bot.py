import time
import threading
from pathlib import Path

import psutil
import telebot

TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
REPORT_INTERVAL = 60

subscribers = set()
subscribers_lock = threading.Lock()


def get_system_report():
    """Collect CPU, memory, disk, uptime, and process count."""
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.cwd().anchor)
    uptime = max(0, int(time.time() - psutil.boot_time()))
    days, remainder = divmod(uptime, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes = remainder // 60
    gib = 1024 ** 3

    return (
        "SYSTEM STATUS\n\n"
        f"CPU usage: {cpu:.1f}%\n"
        f"RAM usage: {memory.percent:.1f}%\n"
        f"Available RAM: {memory.available / gib:.2f} GiB\n"
        f"Disk usage: {disk.percent:.1f}%\n"
        f"Free disk space: {disk.free / gib:.2f} GiB\n"
        f"Uptime: {days} days, {hours} hours, {minutes} minutes\n"
        f"Running processes: {len(psutil.pids())}"
    )


def automatic_reports(bot):
    """Send a report every REPORT_INTERVAL seconds to subscribed chats."""
    while True:
        time.sleep(REPORT_INTERVAL)
        with subscribers_lock:
            chat_ids = list(subscribers)
        if not chat_ids:
            continue
        try:
            report = get_system_report()
        except Exception as error:
            print(f"Could not collect system data: {type(error).__name__}")
            continue
        for chat_id in chat_ids:
            try:
                bot.send_message(chat_id, report)
            except Exception as error:
                print(f"Could not send report: {type(error).__name__}")


def main():
    """Create the bot, register commands, and start monitoring."""
    if TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("Replace TOKEN with your Telegram bot token from BotFather.")
        return

    bot = telebot.TeleBot(TOKEN)

    @bot.message_handler(commands=["start", "help"])
    def send_help(message):
        bot.send_message(
            message.chat.id,
            "System Monitoring Bot\n\n"
            "/status - Show current system status\n"
            "/monitor - Enable reports every 60 seconds\n"
            "/stop - Disable automatic reports"
        )

    @bot.message_handler(commands=["status"])
    def send_status(message):
        bot.send_message(message.chat.id, get_system_report())

    @bot.message_handler(commands=["monitor"])
    def start_monitoring(message):
        with subscribers_lock:
            subscribers.add(message.chat.id)
        bot.send_message(message.chat.id, "Automatic reports enabled.")
        send_status(message)

    @bot.message_handler(commands=["stop"])
    def stop_monitoring(message):
        with subscribers_lock:
            subscribers.discard(message.chat.id)
        bot.send_message(message.chat.id, "Automatic reports disabled.")

    threading.Thread(target=automatic_reports, args=(bot,), daemon=True).start()
    print("Bot is running. Open Telegram and send /start.")
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    main()
