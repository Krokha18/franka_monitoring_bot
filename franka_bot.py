import os
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import telebot

from logger import init_logger
from webdriver_utils import init_webdriver, check_tickets
from io_utils import load_titles_df, load_card_df, load_csv_db, save_csv_db
from general_utils import short_message, full_message

# --- Ініціалізація ---
init_logger()
load_dotenv()

# Шляхи до файлів
event_card_file = os.getenv("EVENT_CARD_FILE")
monitoring_titles_file = os.getenv("MONITORING_TITLES_FILE")

# Завантаження даних
event_card_df = load_card_df(event_card_file)
monitoring_titles_df = load_titles_df(monitoring_titles_file)


def main():
    event_tickets_db_file = os.getenv("EVENT_TICKETS_DB_FILE")
    event_tickets_db = load_csv_db(event_tickets_db_file)

    merged = monitoring_titles_df.merge(event_card_df, on=['title'], how='left').dropna(subset=['link'])
    merged['number'] = merged['number'].astype(int)
    merged['duration_min'] = merged['duration_min'].astype(int)
    merged = merged[merged['min_date'].isna() | (merged['datetime'] >= merged['min_date'])]
    merged = merged[merged['max_date'].isna() | (merged['datetime'] <= merged['max_date'])]
    merged.drop(columns=['min_date', 'max_date', 'parsed_at'], inplace=True)

    driver, wait = init_webdriver()
    unique_links = merged['link'].unique()
    result_dict = {link: check_tickets(link, driver, wait) for link in unique_links}
    merged['free_tickets'] = merged['link'].map(lambda link: result_dict.get(link, (0, {}))[0])
    merged['tickets_summary'] = merged['link'].map(lambda link: result_dict.get(link, (0, {}))[1])
    driver.quit()
    del driver, wait

    merged['short_message'] = merged.apply(lambda row: short_message(row.free_tickets, row.tickets_summary),axis=1)
    merged['full_message'] = merged.apply(lambda row: full_message(row.title, row.link, row.weekday, row.datetime, row.free_tickets, row.tickets_summary),axis=1)
    merged = merged.merge(event_tickets_db.rename(columns={'free_tickets': 'prev_count'}), on=['user_id','link'], how='left')

    mask = (merged['prev_count'].isna()|(merged['free_tickets']!=merged['prev_count']))
    new_tickets_found = mask.sum()>0

    if new_tickets_found:
        event_tickets_db = merged[['user_id','link', 'free_tickets','last_update','short_message']].rename(columns={'short_message':"message"}).drop_duplicates(subset=['user_id','link','free_tickets'])
        event_tickets_db['last_update'] = datetime.now().strftime("%d.%m.%Y %H:%M")
        save_csv_db(event_tickets_db, event_tickets_db_file)

        messages_df = merged[mask][['user_id', 'full_message']].groupby(by=['user_id']).sum().reset_index()
        messages_df['full_message'] = "З'явились нові квитки або зміни у наявності:\n" + messages_df['full_message']
        bot = telebot.TeleBot(os.getenv("TELEGRAM_BOT_TOKEN"))
        messages_df.apply(lambda row: bot.send_message(row.user_id,row.full_message, parse_mode='Markdown', disable_web_page_preview=True), axis=1)


if __name__ == "__main__":
    main()