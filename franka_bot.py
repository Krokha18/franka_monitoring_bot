from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service # Додано
from selenium.webdriver.support import expected_conditions as EC
import telebot
import json
import os
import re
import logging
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Logging
try:
    import systemd.journal
    journal_handler = systemd.journal.JournalHandler()
    journal_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(journal_handler)
    logging.getLogger().setLevel(logging.INFO)
except ImportError:
    logging.basicConfig(
        filename='bot.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

titles_file = "monitoring_titles.json"

def load_titles():
    if os.path.exists(titles_file):
        with open(titles_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_titles(titles):
    with open(titles_file, "w", encoding="utf-8") as f:
        json.dump(titles, f, ensure_ascii=False, indent=4)

monitoring_titles = load_titles()

db_file = "event_tickets_db.json"

def load_db():
    if os.path.exists(db_file):
        with open(db_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_db(db):
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

event_tickets_db = load_db()

# Setup selenium
chrome_options = Options()
chrome_options.binary_location = "/usr/bin/chromium-browser"
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--window-size=1920,1080")

webdriver_service = Service('/usr/bin/chromedriver')
driver = webdriver.Chrome(service = webdriver_service, options=chrome_options)

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
    save_db(event_tickets_db)
    if new_tickets_found:
        send_message(text=message)

    driver.quit()

