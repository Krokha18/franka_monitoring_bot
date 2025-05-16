import os
import telebot
from dotenv import load_dotenv
from io_utils import load_titles, save_titles
from franka_bot import titles_file

load_dotenv()
token = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(token)

@bot.message_handler(commands=['add'])
def add_title(message):
    new_title = message.text[len('/add'):].strip()
    if not new_title:
        bot.reply_to(message, "❗ Вкажіть назву вистави після /add")
        return

    titles = load_titles(titles_file)
    if new_title in titles:
        bot.reply_to(message, f"✅ Вистава *{new_title}* вже в списку", parse_mode='Markdown')
    else:
        titles.append(new_title)
        save_titles(titles, titles_file)
        bot.reply_to(message, f"➕ Додано виставу: *{new_title}*", parse_mode='Markdown')

@bot.message_handler(commands=['remove'])
def remove_title(message):
    title_to_remove = message.text[len('/remove'):].strip()
    titles = load_titles(titles_file)
    if title_to_remove not in titles:
        bot.reply_to(message, f"⚠️ Вистави *{title_to_remove}* немає в списку", parse_mode='Markdown')
    else:
        titles.remove(title_to_remove)
        save_titles(titles, titles_file)
        bot.reply_to(message, f"➖ Видалено виставу: *{title_to_remove}*", parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_titles(message):
    titles = load_titles(titles_file)
    if not titles:
        bot.reply_to(message, "📭 Список моніторингу порожній")
    else:
        formatted = "\n".join([f"- {t}" for t in titles])
        bot.reply_to(message, f"📌 Вистави у моніторингу:\n{formatted}")

if __name__ == "__main__":
    print("Bot commands listener started...")
    bot.infinity_polling()
