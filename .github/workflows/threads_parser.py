# threads_parser.py
"""
Daily Threads scraper:
— вытягивает свежие посты по ключевым словам,
— оставляет только «залетевшие» (метрики и пороги ниже),
— шлёт список вам в Telegram.
Опционально добавляет краткую GPT-3.5 аннотацию «почему пост зашёл».
"""

import os
import datetime
import pandas as pd
from threads_client import Threads
from telegram import Bot
from telegram.constants import ParseMode

# --- НАСТРОЙКИ -------------------------------------------
KEYWORDS = [
    "marketing", "business", "psychology",
    "growth", "founder", "humor marketing", "copywriting"
]
MIN_VIEWS = 40_000      # ≥ 40 000 просмотров
LIKE_RATIO = 0.30       # лайков ≥ 30 %
COMMENT_RATIO = 0.15    # комментариев ≥ 15 %
MAX_POSTS = 300         # сколько постов запрашивать на ключевое слово
# ----------------------------------------------------------

USE_LLM_SUMMARY = bool(os.getenv("OPENAI_API_KEY"))


def fetch_posts() -> list[dict]:
    """Берём посты через неофициальный Threads-API."""
    th = Threads(os.getenv("THREADS_USERNAME"), os.getenv("THREADS_PASSWORD"))
    all_posts = []
    for kw in KEYWORDS:
        posts = th.search_posts(query=kw, limit=MAX_POSTS)
        for p in posts:
            if p["view_count"] is None:      # иногда скрыто
                continue
            p["keyword"] = kw
            all_posts.append(p)
    return all_posts


def filter_posts(posts: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(posts)
    df = df[
        (df.view_count >= MIN_VIEWS)
        & (df.like_count / df.view_count >= LIKE_RATIO)
        & (df.reply_count / df.view_count >= COMMENT_RATIO)
    ]
    return df.sort_values("view_count", ascending=False)


def build_message(df: pd.DataFrame) -> str:
    lines = [f"🔥 *Top Threads* — {datetime.date.today():%d %b %Y}"]
    for _, row in df.head(10).iterrows():
        url = f"https://www.threads.net/t/{row['code']}"
        ratios = (
            f"👍{row.like_count:,}  💬{row.reply_count:,}  👀{row.view_count:,}"
        )
        lines.append(f"• [{row['keyword']}] {ratios}\n{url}")
    return "\n\n".join(lines)


def send_telegram(text: str) -> None:
    bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
    bot.send_message(
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
    )


def main():
    posts = fetch_posts()
    df = filter_posts(posts)
    if df.empty:
        print("No viral posts today 😴")
        return

    send_telegram(build_message(df))

    # ---- Опциональная GPT-аннотация ----------------------
    if USE_LLM_SUMMARY:
        from openai import OpenAI

        client = OpenAI()
        prompt = (
            "In one tweet-style paragraph, explain why these Threads posts "
            "went viral. Focus on hooks, emotion and clarity.\n\n"
            + "\n".join(df.text.head(3))
        )
        summary = (
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=80,
            )
            .choices[0]
            .message.content.strip()
        )
        send_telegram("🧠 *Why it works*\n\n" + summary)


if __name__ == "__main__":
    main()
