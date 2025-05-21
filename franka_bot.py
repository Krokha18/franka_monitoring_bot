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
from io_utils import load_db, save_db
from general_utils import normalize_month, format_ticket_count

# --- Ініціалізація ---
init_logger()
load_dotenv()
driver, wait = init_webdriver()

# Шляхи до файлів
event_file = os.getenv("EVENT_CARD_FILE", 'all_event_card.csv')
monitoring_file = os.getenv("MONITORING_TITLES_FILE", "monitoring_titles.csv")
db_file = "event_tickets_db.json"

# Завантаження даних
event_tickets_db = load_db(db_file)
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
    message = "З'явились нові квитки або зміни у наявності:"
    new_tickets_found = False

    event_df["datetime"] = event_df.apply(parse_event_date, axis=1)

    for _, monitor in monitoring_df.iterrows():
        title = monitor["title"].strip()
        min_date = monitor.get("min_date", pd.NaT)
        max_date = monitor.get("max_date", pd.NaT)

        filtered_events = event_df[event_df["title"].str.strip() == title]

        if pd.notna(min_date):
            filtered_events = filtered_events[filtered_events["datetime"] >= min_date]
        if pd.notna(max_date):
            filtered_events = filtered_events[filtered_events["datetime"] <= max_date]

        if filtered_events.empty:
            logging.info(f"Немає подій для '{title}' у вказаному діапазоні.")
            continue

        for _, row in filtered_events.iterrows():
            link = row["link"]
            event_date_str = row["datetime"].strftime("%d.%m.%Y %H:%M")

            free_tickets, ticket_summary = check_tickets(link)
            logging.info(f'{free_tickets} tickets for "{title}" on {event_date_str}')

            prev_count = event_tickets_db.get(link, 0)

            if free_tickets > prev_count:
                event_tickets_db[link] = free_tickets
                ticket_details = "\n".join(
                    [f"- {format_ticket_count(c)} по {p} грн" for p, c in sorted(ticket_summary.items())]
                )
                message += f'\n[{title}]({link}) *{event_date_str}* — доступно місць {free_tickets}:\n{ticket_details}\n'
                new_tickets_found = True
            elif free_tickets == 0 and prev_count > 0:
                event_tickets_db[link] = 0
                message += f'\n[{title}]({link}) *{event_date_str}* — всі квитки розпродані.\n'
                new_tickets_found = True

    save_db(event_tickets_db, db_file)
    if new_tickets_found:
        send_message(message)
    driver.quit()

if __name__ == "__main__":
    main()
