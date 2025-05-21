import os
import telebot
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

monitoring_file = os.getenv("MONITORING_TITLES_FILE", "monitoring_titles.csv")
load_dotenv()
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))

DATE_FMT = "%Y-%m-%d"

def load_monitoring_df():
    if os.path.exists(monitoring_file):
        return pd.read_csv(monitoring_file, parse_dates=["min_date", "max_date"])
    return pd.DataFrame(columns=["title", "min_date", "max_date"])

def save_monitoring_df(df):
    df.to_csv(monitoring_file, index=False)

@bot.message_handler(commands=["add"])
def add_title(message):
    args = message.text[len('/add'):].strip().split('|')
    if len(args) < 1:
        bot.reply_to(message, "❗ Формат: /add Назва | min_date | max_date (дати не обов'язкові)")
        return

    title = args[0].strip()
    min_date = pd.to_datetime(args[1].strip(), format=DATE_FMT, errors='coerce') if len(args) > 1 else pd.NaT
    max_date = pd.to_datetime(args[2].strip(), format=DATE_FMT, errors='coerce') if len(args) > 2 else pd.NaT

    df = load_monitoring_df()

    if title in df["title"].values:
        bot.reply_to(message, f"⚠️ '{title}' вже у списку. Видаліть перед додаванням заново або скористайтесь /update")
        return

    new_row = pd.DataFrame([{"title": title, "min_date": min_date, "max_date": max_date}])
    df = pd.concat([df, new_row], ignore_index=True)
    save_monitoring_df(df)
    bot.reply_to(message, f"✅ Додано: *{title}*\n🗓 {min_date.date() if pd.notna(min_date) else '---'} → {max_date.date() if pd.notna(max_date) else '---'}", parse_mode='Markdown')

@bot.message_handler(commands=["remove"])
def remove_title(message):
    title = message.text[len("/remove"):].strip()
    df = load_monitoring_df()
    if title not in df["title"].values:
        bot.reply_to(message, f"⚠️ Вистави *{title}* немає в списку", parse_mode='Markdown')
        return
    df = df[df["title"] != title]
    save_monitoring_df(df)
    bot.reply_to(message, f"➖ Видалено: *{title}*", parse_mode='Markdown')

@bot.message_handler(commands=["list"])
def list_titles(message):
    df = load_monitoring_df()
    if df.empty:
        bot.reply_to(message, "📭 Список моніторингу порожній")
        return
    lines = []
    for _, row in df.iterrows():
        min_d = row["min_date"].date().isoformat() if pd.notna(row["min_date"]) else "---"
        max_d = row["max_date"].date().isoformat() if pd.notna(row["max_date"]) else "---"
        lines.append(f"- *{row['title']}* ({min_d} → {max_d})")
    bot.reply_to(message, "🎭 Вистави у моніторингу:\n" + "\n".join(lines), parse_mode="Markdown")

@bot.message_handler(commands=["update"])
def update_title(message):
    args = message.text[len('/update'):].strip().split('|')
    if len(args) < 2:
        bot.reply_to(message, "❗ Формат: /update Назва | новий_min | новий_max")
        return

    title = args[0].strip()
    min_date = pd.to_datetime(args[1].strip(), format=DATE_FMT, errors='coerce') if len(args) > 1 else pd.NaT
    max_date = pd.to_datetime(args[2].strip(), format=DATE_FMT, errors='coerce') if len(args) > 2 else pd.NaT

    df = load_monitoring_df()
    if title not in df["title"].values:
        bot.reply_to(message, f"⚠️ Вистави *{title}* немає в списку", parse_mode='Markdown')
        return

    df.loc[df["title"] == title, "min_date"] = min_date
    df.loc[df["title"] == title, "max_date"] = max_date
    save_monitoring_df(df)
    bot.reply_to(message, f"🔁 Оновлено: *{title}*\n🗓 {min_date.date() if pd.notna(min_date) else '---'} → {max_date.date() if pd.notna(max_date) else '---'}", parse_mode='Markdown')

if __name__ == "__main__":
    print("Bot commands listener started...")
    bot.infinity_polling()