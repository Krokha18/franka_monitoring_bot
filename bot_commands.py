import os
import telebot
import pandas as pd
from dotenv import load_dotenv
from monitoring_service import add_title, remove_title, update_title, list_titles

load_dotenv()
monitoring_file = os.getenv("MONITORING_TITLES_FILE")
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))

DATE_FMT = "%Y-%m-%d"

def parse_date(s):
    return pd.to_datetime(s.strip(), format=DATE_FMT, errors='coerce')

@bot.message_handler(commands=["add"])
def handle_add(message):
    args = message.text[len('/add'):].strip().split('|')
    if len(args) < 1 or not args[0].strip():
        bot.reply_to(message, "❗ Формат: /add Назва | min_date | max_date (дати не обов'язкові)")
        return

    title = args[0].strip()
    min_date = parse_date(args[1]) if len(args) > 1 else pd.NaT
    max_date = parse_date(args[2]) if len(args) > 2 else pd.NaT

    if not add_title(monitoring_file, title, min_date, max_date):
        bot.reply_to(message, f"⚠️ '{title}' вже у списку. Видаліть перед додаванням заново або скористайтесь /update")
        return

    bot.reply_to(
        message,
        f"✅ Додано: *{title}*\n🗓 {min_date.date() if pd.notna(min_date) else '---'} → {max_date.date() if pd.notna(max_date) else '---'}",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=["remove"])
def handle_remove(message):
    title = message.text[len("/remove"):].strip()
    if not title:
        bot.reply_to(message, "❗ Формат: /remove Назва")
        return

    if not remove_title(monitoring_file, title):
        bot.reply_to(message, f"⚠️ Вистави *{title}* немає в списку", parse_mode='Markdown')
        return

    bot.reply_to(message, f"➖ Видалено: *{title}*", parse_mode='Markdown')

@bot.message_handler(commands=["list"])
def handle_list(message):
    df = list_titles(monitoring_file)
    if df.empty:
        bot.reply_to(message, "📭 Список моніторингу порожній")
        return

    lines = []
    for _, row in df.iterrows():
        min_d = pd.to_datetime(row["min_date"]).date() if pd.notna(row["min_date"]) else "---"
        max_d = pd.to_datetime(row["max_date"]).date() if pd.notna(row["max_date"]) else "---"
        lines.append(f"- *{row['title']}* ({min_d} → {max_d})")

    bot.reply_to(message, "🎭 Вистави у моніторингу:\n" + "\n".join(lines), parse_mode="Markdown")

@bot.message_handler(commands=["update"])
def handle_update(message):
    args = message.text[len('/update'):].strip().split('|')
    if len(args) < 2 or not args[0].strip():
        bot.reply_to(message, "❗ Формат: /update Назва | новий_min | новий_max")
        return

    title = args[0].strip()
    min_date = parse_date(args[1]) if len(args) > 1 else pd.NaT
    max_date = parse_date(args[2]) if len(args) > 2 else pd.NaT

    if not update_title(monitoring_file, title, min_date, max_date):
        bot.reply_to(message, f"⚠️ Вистави *{title}* немає в списку", parse_mode='Markdown')
        return

    bot.reply_to(
        message,
        f"🔁 Оновлено: *{title}*\n🗓 {min_date.date() if pd.notna(min_date) else '---'} → {max_date.date() if pd.notna(max_date) else '---'}",
        parse_mode='Markdown'
    )

if __name__ == "__main__":
    print("Bot commands listener started...")
    bot.infinity_polling()
