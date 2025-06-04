import logging
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service # Додано

from logger import init_logger
init_logger()

from dotenv import load_dotenv
load_dotenv()


def init_webdriver():
    try:
        # Setup selenium
        chrome_options = Options()
        chrome_options.binary_location = os.getenv("CHROMIUM_BIN","/usr/bin/chromium-browser")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        webdriver_service = Service(os.getenv("CHROMEDRIVER_BIN",'/usr/bin/chromedriver'))
        driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        wait = WebDriverWait(driver, 10)
        return driver, wait
    except Exception as e:
        logging.error(f"Не вдалося завантажити Chromium WebDriver. {e}")
        return None, None

def check_tickets(event_link, driver, wait):
    logging.info(f'Checking tickets for {event_link}')
    driver.get(event_link)

    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "ticketSelection__wrapper")))
    except Exception as e:
        logging.warning(f"Не вдалося завантажити квитки. {e}")
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
