import os
import re
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import telebot

from logger import init_logger
from webdriver_utils import init_webdriver
from io_utils import load_csv_db, save_csv_db
from general_utils import normalize_month, format_ticket_count, normalize_weekday

# --- Ініціалізація ---
init_logger()
load_dotenv()
driver, wait = init_webdriver()

# Шляхи до файлів
event_file = os.getenv("EVENT_CARD_FILE", 'all_event_card.csv')
monitoring_file = os.getenv("MONITORING_TITLES_FILE", "monitoring_titles.csv")

# Завантаження даних
event_df = pd.read_csv(event_file)
monitoring_df = pd.read_csv(monitoring_file, parse_dates=['min_date', 'max_date'])

# --- Функції ---

def check_tickets(event_link):
    logging.info(f'Checking tickets for {event_link}')
    driver.get(event_link)

    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ticketSelection__wrapper")))
    except Exception:
        logging.warning("Не вдалося завантажити квитки.")
        return 0, {}

    try:
        wrapper = driver.find_element(By.CLASS_NAME, "ticketSelection__wrapper")
        all_tickets = wrapper.find_elements(By.CSS_SELECTOR, "rect.tooltip-button")
        busy = wrapper.find_elements(By.CSS_SELECTOR, "rect.occupied.tooltip-button")
        busy_inclusive = wrapper.find_elements(By.CSS_SELECTOR, "rect.occupied.tooltip-button.inclusive")
        busy_set = set(busy + busy_inclusive)

        free_tickets = []
        for ticket in all_tickets:
            if ticket not in busy_set and ticket.get_attribute('fill') != '#ADADAD':
                title = ticket.get_attribute('title') or "Unknown"
                price_match = re.search(r"Ціна:\s*([\d,]+)", title)
                if price_match:
                    price = int(price_match.group(1).replace(',', ''))
                    free_tickets.append(price)

        ticket_summary = {}
        for price in free_tickets:
            ticket_summary[price] = ticket_summary.get(price, 0) + 1

        return len(free_tickets), ticket_summary
    except Exception as e:
        logging.warning(f"Не вдалося зчитати квитки: {e}")
        return 0, {}

def send_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    group_id = int(os.getenv("TELEGRAM_GROUP_ID"))
    bot = telebot.TeleBot(token)
    bot.send_message(group_id, text, parse_mode='Markdown', disable_web_page_preview=True)

def parse_event_date(row):
    try:
        day = int(row['number'])
        month = normalize_month(row['month'])
        current_year = datetime.now().year
        date_str = f"{current_year}-{month}-{day:02d} {row['start_time']}"
        return pd.to_datetime(date_str, format='%Y-%m-%d %H:%M')
    except Exception as e:
        logging.warning(f"Не вдалося спарсити дату: {e}")
        return pd.NaT

# --- Основна логіка ---

def main():
    db_file = os.getenv("EVENT_TICKETS_DB_FILE","event_tickets_db.csv")
    event_tickets_db = load_csv_db(db_file)

    # Інверсований індекс для швидкого доступу до записів по посиланню
    db_index = {row["link"]: i for i, row in event_tickets_db.iterrows()}

    message = "З'явились нові квитки або зміни у наявності:"
    new_tickets_found = False
    new_rows = []

    # Парсимо дати подій
    event_df["datetime"] = event_df.apply(parse_event_date, axis=1)

    # Перебираємо всі події
    for _, row in event_df.iterrows():
        link = row["link"]
        title = row["title"].strip()
        weekday = row["weekday"]
        event_datetime = row["datetime"]

        # Перевірка, чи ця подія входить у monitoring_df
        monitor_match = monitoring_df[monitoring_df["title"].str.strip() == title]
        if monitor_match.empty:
            continue

        # Фільтрація по даті для кожного монітора
        keep = False
        for _, monitor in monitor_match.iterrows():
            min_date = monitor.get("min_date", pd.NaT)
            max_date = monitor.get("max_date", pd.NaT)

            if pd.notna(min_date) and event_datetime < min_date:
                continue
            if pd.notna(max_date) and event_datetime > max_date:
                continue
            keep = True
            break

        if not keep:
            continue

        event_date_str = event_datetime.strftime("%d.%m.%Y %H:%M")
        event_date_str = f"{normalize_weekday(weekday)}, {event_date_str}"

        # Отримання квитків
        free_tickets, ticket_summary = check_tickets(link)
        logging.info(f'{free_tickets} tickets for "{title}" on {event_date_str}')

        # Формування повідомлення
        if free_tickets > 0:
            ticket_details = "\n".join(
                [f"- {format_ticket_count(c)} по {p} грн" for p, c in sorted(ticket_summary.items())]
            )
            tickets_msg = f'доступно місць {free_tickets}:\n{ticket_details}'
        else:
            tickets_msg = 'всі квитки розпродані'
        
        title_part = f'[{title}]({link}) *{event_date_str}*'
        msg = f'{title_part} — {tickets_msg}.\n'

        # Перевірка зміни
        prev_count = event_tickets_db.loc[db_index[link], "free_tickets"] if link in db_index else -1
        if free_tickets != prev_count:
            new_tickets_found = True
            message += "\n" + msg
            logging.info(f"🔄 Зміна по {link}: {prev_count} → {free_tickets}")

        # Додаємо запис
        new_rows.append({
            "link": link,
            "free_tickets": free_tickets,
            "last_update": datetime.now(),
            "message": tickets_msg
        })

    # Оновлення всієї бази
    if new_rows:
        event_tickets_db = pd.DataFrame(new_rows)
        save_csv_db(event_tickets_db, db_file)

    if new_tickets_found:
        send_message(message)

    driver.quit()


if __name__ == "__main__":
    main()
