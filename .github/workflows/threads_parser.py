# threads_parser.py
import os
import datetime
from telegram import Bot

def main():
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    bot.send_message(
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        text=f"✅ GitHub Actions работает! {ts}",
        disable_web_page_preview=True
    )

if __name__ == "__main__":
    main()
