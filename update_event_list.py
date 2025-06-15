import pandas as pd
import os
import logging
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from logger import init_logger
init_logger()

from dotenv import load_dotenv
load_dotenv()

from webdriver_utils import init_webdriver

from general_utils import parse_event_date, normalize_month


def get_max_pages(driver, wait):
    driver.get('https://sales.ft.org.ua/events')
    try:
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'pagination__item')))
        items = driver.find_elements(By.CLASS_NAME, 'pagination__item')
        if len(items) >= 2:
            return int(items[-2].text.strip())
    except Exception as e:
        logging.error(f"Помилка в get_max_pages: {e}")
    return 1


def get_all_event_card(event_file, driver, wait):
    results_list = []
    start_page, max_pages = 1, get_max_pages(driver, wait)
    for page in range(start_page, max_pages + 1):
        url = f'https://sales.ft.org.ua/events?page={page}'
        logging.info(f'Parsing page {page}')
        driver.get(url)

        try:
            # Очікуємо появу принаймні одного елементу-картки
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'performanceCard')))
            cards = driver.find_elements(By.CLASS_NAME, 'performanceCard')
        except Exception as e:
            logging.warning(f"Не вдалося завантажити картки на сторінці {page}: {e}")
            continue

        for card in cards:
            try:
                title = card.find_element(By.CLASS_NAME, 'performanceCard__title').text.strip().replace('’',"'")
                date_time = card.find_element(By.CLASS_NAME, 'performanceCard__author').text
                weekday, date = date_time.split(", ")
                number, month, start_time = date.split(" ")
                dt_now = datetime.now()
                hours, minutes = start_time.split(":")
                start_dt = datetime(dt_now.year, int(normalize_month(month)), int(number), int(hours)-1, int(minutes))
                if start_dt > dt_now:
                    duration_min = int(card.find_element(By.CLASS_NAME, 'performanceCard__time-val').text)
                    link = card.get_attribute('href').strip()
                    results_list.append({
                        "link": link,
                        "title": title,
                        "weekday": weekday,
                        "number": int(number),
                        "month": month,
                        "start_time": start_time,
                        "duration_min": duration_min,
                        "parsed_at": datetime.now().isoformat()
                    })
            except Exception as e:
                logging.warning(f"Помилка в читанні картки: {e}")

    updates_df = pd.DataFrame(results_list)
    updates_df['datetime'] = updates_df.apply(parse_event_date, axis=1)
    updates_df.to_csv(event_file, index=False)
    driver.quit()
    return updates_df


if __name__ == "__main__":
    driver, wait = init_webdriver()
    get_all_event_card(os.getenv("EVENT_CARD_FILE"), driver, wait)
    driver.quit()

