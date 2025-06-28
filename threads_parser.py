import os
import datetime
import pandas as pd
from threads_api.src.threads_api import ThreadsAPI as Threads
from threads_api import ThreadsAPI as Threads
from telegram import Bot
from telegram.constants import ParseMode

# ====== Настройки фильтрации ======
KEYWORDS = ["business", "marketing", "psychology", "growth", "founder"]
MIN_VIEWS = 40_000
LIKE_RATIO = 0.30
COMMENT_RATIO = 0.15
MAX_POSTS = 300

def fetch_posts():
    th = Threads(os.getenv("THREADS_USERNAME"), os.getenv("THREADS_PASSWORD"))
    posts = []
    for kw in KEYWORDS:
        for p in th.search_posts(query=kw, limit=MAX_POSTS):
            if p.get("view_count"):
                p["keyword"] = kw
                posts.append(p)
    return posts

def filter_posts(posts):
    df = pd.DataFrame(posts)
    if df.empty:
        return df
    df = df[
        (df.view_count >= MIN_VIEWS) &
        (df.like_count / df.view_count >= LIKE_RATIO) &
        (df.reply_count / df.view_count >= COMMENT_RATIO)
    ]
    return df.sort_values("view_count", ascending=False)

def build_message(df):
    today = datetime.date.today().strftime("%d %b %Y")
    lines = [f"🔥 *Top Threads* — {today}"]
    for _, r in df.head(10).iterrows():
        url = f"https://www.threads.net/t/{r['code']}"
        stats = f"👍{r.like_count:,} 💬{r.reply_count:,} 👀{r.view_count:,}"
        lines.append(f"• [{r['keyword']}] {stats}\n{url}")
    return "\n\n".join(lines)

def send(text):
    Bot(token=os.getenv("TELEGRAM_BOT_TOKEN")).send_message(
        chat_id=os.getenv("TELEGRAM_CHAT_ID"),
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True
    )

def main():
    posts = fetch_posts()
    df = filter_posts(posts)
    if df.empty:
        send("ℹ️ Сегодня не нашлось «залётных» тредов, но я жив и готов завтра!")
    else:
        send(build_message(df))

if __name__ == "__main__":
    main()
