import requests
from bs4 import BeautifulSoup
import time
import telebot
import json
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
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

monitoring_titles = [
    r"Тартюф",
    r"Кайдашева сім'я",
    r"Конотопська відьма",
    r"Безталанна",

]

token = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID"))
bot = telebot.TeleBot(token)

session = requests.Session()
session.headers.update({
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
})

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

def get_max_pages():
    url = 'https://sales.ft.org.ua/events'
    response = session.get(url)
    if response.status_code != 200:
        logging.error(f"Помилка завантаження сторінки: {url} (Статус: {response.status_code})")
        return 1
    soup = BeautifulSoup(response.text, 'html.parser')
    pagination_items = soup.find_all("li", class_="pagination__item")
    if pagination_items:
        last_page = pagination_items[-2].find("a")
        if last_page:
            return int(last_page.text.strip())
    return 1

def get_all_event_card():
    cards_dict = {}
    for page in range(1, get_max_pages() + 1):
        url = f'https://sales.ft.org.ua/events?page={page}'
        logging.info(f'Parsing page {page}')
        response = session.get(url)
        if response.status_code != 200:
            logging.error(f"Помилка завантаження сторінки: {url} (Статус: {response.status_code})")
            continue
        soup = BeautifulSoup(response.text, 'html.parser')
        for card in soup.find_all("a", class_="performanceCard"):
            title = card.find("h3", class_="performanceCard__title").text.strip()
            link = card["href"].strip()
            cards_dict.setdefault(title, []).append(link)
        time.sleep(0.4)
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
    response = session.get(event_link)
    if response.status_code != 200:
        logging.error(f"Помилка завантаження сторінки події: {event_link} (Статус: {response.status_code})")
        return 0, {}
    soup = BeautifulSoup(response.text, "html.parser")
    tickets = soup.find(class_='ticketSelection__wrapper')
    if not tickets:
        return 0, {}
    all_tickets = tickets.find_all("rect", class_="tooltip-button")
    busy_tickets = tickets.find_all("rect", class_="occupied tooltip-button")
    busy_tickets_inclusive = tickets.find_all("rect", class_="occupied tooltip-button inclusive")
    free_tickets = [
        {
            "price": int(ticket.get("title", "Unknown").split("Ціна: ")[-1].split()[0]),
            "title": ticket.get("title", "Unknown")
        }
        for ticket in all_tickets if ticket not in busy_tickets + busy_tickets_inclusive and ticket.get('fill') != '#ADADAD'
    ]
    ticket_summary = {}
    for ticket in free_tickets:
        price = ticket["price"]
        ticket_summary[price] = ticket_summary.get(price, 0) + 1
    return len(free_tickets), ticket_summary

def send_message(text):
    bot.send_message(TELEGRAM_GROUP_ID, text, parse_mode='Markdown', disable_web_page_preview=True)

if __name__ == "__main__":
    all_cards = get_all_event_card()
    message = "З'явились нові квитки або зміни у наявності:\n"
    new_tickets_found = False
    for title in monitoring_titles:
        if title not in all_cards:
            logging.warning(f'{title} not present in the cards.')
            continue
        logging.info(f'Checking available tickets for {title}')
        for link in all_cards[title]:
            free_tickets, ticket_summary = check_tickets(link)
            logging.info(f'Found {free_tickets} tickets for {title} with {link}')
            if link in event_tickets_db:
                previous_count = event_tickets_db[link]
                if free_tickets > previous_count:
                    event_tickets_db[link] = free_tickets
                    ticket_details = "\n".join([f"- {format_ticket_count(count)} по {price} гривень" for price, count in sorted(ticket_summary.items())])
                    message += f'\n[{title}]({link}) доступно місць {free_tickets}:\n{ticket_details}\n'
                    new_tickets_found = True
                elif free_tickets == 0 and previous_count > 0:
                    message += f'\n[{title}]({link}) всі квитки розпродані.\n'
                    event_tickets_db[link] = 0
                    new_tickets_found = True
            else:
                event_tickets_db[link] = free_tickets
                if free_tickets > 0:
                    ticket_details = "\n".join([f"- {format_ticket_count(count)} по {price} гривень" for price, count in sorted(ticket_summary.items())])
                    message += f'\n[{title}]({link}) доступно місць {free_tickets}:\n{ticket_details}\n'
                    new_tickets_found = True
    save_db(event_tickets_db)
    if new_tickets_found:
        send_message(text=message)
