import os
import telebot
import pandas as pd
from dotenv import load_dotenv
from monitoring_service import add_title, remove_title, update_title, list_titles
from general_utils import format_row, parse_date

load_dotenv()
monitoring_file = os.getenv("MONITORING_TITLES_FILE")
bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))


@bot.message_handler(commands=["add"])
def handle_add(message):
    args = message.text[len("/add"):].strip().split("|")
    if len(args) < 1 or not args[0].strip():
        bot.reply_to(message, "❗ Формат: /add Назва | min_date | max_date (дати не обов'язкові)")
        return

    title = args[0].strip().replace('’',"'")
    min_date = parse_date(args[1]) if len(args) > 1 else pd.NaT
    max_date = parse_date(args[2]) if len(args) > 2 else pd.NaT
    user_id = message.chat.id

    success = add_title(monitoring_file, user_id, title, min_date, max_date)
    if not success:
        bot.reply_to(message, f"⚠️ '{title}' вже у списку. Скористайтесь /update або /remove")
        return

    bot.reply_to(
        message,
        f"✅ Додано: *{title}*\n🗓 {min_date.date() if pd.notna(min_date) else '---'} → {max_date.date() if pd.notna(max_date) else '---'}",
        parse_mode="Markdown"
    )

@bot.message_handler(commands=["remove"])
def handle_remove(message):
    title = message.text[len("/remove"):].strip().replace('’',"'")
    if not title:
        bot.reply_to(message, "❗ Формат: /remove Назва")
        return

    user_id = message.chat.id
    success = remove_title(monitoring_file, user_id, title)
    if not success:
        bot.reply_to(message, f"⚠️ Вистави *{title}* немає у вашому списку", parse_mode="Markdown")
        return

    bot.reply_to(message, f"➖ Видалено: *{title}*", parse_mode="Markdown")

@bot.message_handler(commands=["list"])
def handle_list(message):
    user_id = message.chat.id
    df = list_titles(monitoring_file, user_id)
    if df.empty:
        bot.reply_to(message, "📭 Ваш список моніторингу порожній")
        return

    lines = df.apply(format_row, axis=1).tolist()
    bot.reply_to(message, "🎭 Ваші вистави:\n" + "\n".join(lines), parse_mode="Markdown")

@bot.message_handler(commands=["update"])
def handle_update(message):
    args = message.text[len("/update"):].strip().split("|")
    if len(args) < 2 or not args[0].strip():
        bot.reply_to(message, "❗ Формат: /update Назва | новий_min | новий_max")
        return

    title = args[0].strip().replace('’',"'")
    min_date = parse_date(args[1]) if len(args) > 1 else pd.NaT
    max_date = parse_date(args[2]) if len(args) > 2 else pd.NaT
    user_id = message.chat.id

    success = update_title(monitoring_file, user_id, title, min_date, max_date)
    if not success:
        bot.reply_to(message, f"⚠️ Вистави *{title}* немає у вашому списку", parse_mode="Markdown")
        return

    bot.reply_to(
        message,
        f"🔁 Оновлено: *{title}*\n🗓 {min_date.date() if pd.notna(min_date) else '---'} → {max_date.date() if pd.notna(max_date) else '---'}",
        parse_mode="Markdown"
    )

if __name__ == "__main__":
    print("Bot commands listener started...")
    bot.infinity_polling()
