import telebot
import os
import re
import logging
import time
from selenium.webdriver.common.by import By


from logger import init_logger
init_logger()

from dotenv import load_dotenv
load_dotenv()

from io_utils import load_titles
titles_file = "monitoring_titles.json"
monitoring_titles = load_titles(titles_file)

from io_utils import load_db, save_db
db_file = "event_tickets_db.json"
event_tickets_db = load_db(db_file)

from webdriver_utils import init_webdriver
driver = init_webdriver()


def get_max_pages():
    driver.get('https://sales.ft.org.ua/events')
    try:
        items = driver.find_elements(By.CLASS_NAME, 'pagination__item')
        if len(items) >= 2:
            return int(items[-2].text.strip())
    except Exception as e:
        logging.error(f"Помилка в get_max_pages: {e}")
    return 1

def get_all_event_card():
    cards_dict = {}
    for page in range(1, get_max_pages() + 1):
        url = f'https://sales.ft.org.ua/events?page={page}'
        logging.info(f'Parsing page {page}')
        driver.get(url)
        time.sleep(1)  # невелика затримка для завантаження сторінки
        cards = driver.find_elements(By.CLASS_NAME, 'performanceCard')
        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'performanceCard__title').text.strip()
                link = card.get_attribute('href').strip()
                cards_dict.setdefault(title, []).append(link)
            except Exception as e:
                logging.warning(f"Помилка в читанні картки: {e}")
    return cards_dict

def format_ticket_count(count):
    if 11 <= count % 100 <= 19:
        return f"{count} квитків"
    elif count % 10 == 1:
        return f"{count} квиток"
    elif 2 <= count % 10 <= 4:
        return f"{count} квитки"
    else:
        return f"{count} квитків"

def check_tickets(event_link):
    logging.info(f'Checking tickets for {event_link}')
    driver.get(event_link)
    time.sleep(2)
    date_time = "Дата невідома"

    try:
        breadcrumbs = driver.find_elements(By.CSS_SELECTOR, "ul.breadcrumbs__list li.breadcrumbs__item span[itemprop='name']")
        for span in breadcrumbs:
            possible_date = span.text.strip()
            if re.search(r"\d{1,2} .* \d{4}", possible_date):
                date_time = possible_date
                break
    except Exception as e:
        logging.warning(f"Не вдалося знайти дату: {e}")

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
                    raw_price = price_match.group(1).replace(',', '')
                    price = int(raw_price)
                    free_tickets.append({"price": price, "title": title})

        ticket_summary = {}
        for ticket in free_tickets:
            price = ticket["price"]
            ticket_summary[price] = ticket_summary.get(price, 0) + 1

        return len(free_tickets), ticket_summary, date_time
    except Exception as e:
        logging.warning(f"Не вдалося зчитати квитки: {e}")
        return 0, {}, date_time

def send_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID"))
    bot = telebot.TeleBot(token)
    bot.send_message(TELEGRAM_GROUP_ID, text, parse_mode='Markdown', disable_web_page_preview=True)
    

if __name__ == "__main__":
    all_cards = get_all_event_card()
    message = "З'явились нові квитки або зміни у наявності:"
    new_tickets_found = False
    for title in monitoring_titles:
        if title not in all_cards:
            logging.warning(f'{title} not present in the cards.')
            continue
        logging.info(f'Checking available tickets for {title}')
        for link in all_cards[title]:
            free_tickets, ticket_summary, date_time = check_tickets(link)
            logging.info(f'Found {free_tickets} tickets for {title} with {link}')
            if link in event_tickets_db:
                previous_count = event_tickets_db[link]
                if free_tickets > previous_count:
                    event_tickets_db[link] = free_tickets
                    ticket_details = "\n".join([f"- {format_ticket_count(count)} по {price} гривень" for price, count in sorted(ticket_summary.items())])
                    message += f'\n[{title}]({link}) ({date_time}) доступно місць {free_tickets}:\n{ticket_details}\n'
                    new_tickets_found = True
                elif free_tickets == 0 and previous_count > 0:
                    message += f'\n[{title}]({link}) ({date_time}) всі квитки розпродані.\n'
                    event_tickets_db[link] = 0
                    new_tickets_found = True
            else:
                event_tickets_db[link] = free_tickets
                if free_tickets > 0:
                    ticket_details = "\n".join([f"- {format_ticket_count(count)} по {price} гривень" for price, count in sorted(ticket_summary.items())])
                    message += f'\n[{title}]({link}) ({date_time}) доступно місць {free_tickets}:\n{ticket_details}\n'
                    new_tickets_found = True
    save_db(event_tickets_db, db_file)
    if new_tickets_found:
        send_message(text=message)

    driver.quit()

