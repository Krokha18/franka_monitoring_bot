import pandas as pd
import logging
from datetime import datetime

from logger import init_logger
init_logger()

def format_ticket_count(count):
    if 11 <= count % 100 <= 19:
        return f"{count} квитків"
    elif count % 10 == 1:
        return f"{count} квиток"
    elif 2 <= count % 10 <= 4:
        return f"{count} квитки"
    else:
        return f"{count} квитків"

def normalize_month(month_str):
    month_map = {
        "січня": "01", "лютого": "02", "березня": "03", "квітня": "04",
        "травня": "05", "червня": "06", "липня": "07", "серпня": "08",
        "вересня": "09", "жовтня": "10", "листопада": "11", "грудня": "12"
    }
    return month_map.get(month_str.strip().lower(), "01")

def normalize_weekday(weekday):
    weekday_map = {"ПН":'Понеділок',
                   "ВТ":'Вівторок',
                   "СР":'Середа',
                   "ЧТ":'Четвер',
                   "ПТ":'П\'ятниця',
                   "СБ":'Субота',
                   "НД":'Неділя'}
    return weekday_map.get(weekday, weekday)

def format_row(row):
    min_d = pd.to_datetime(row["min_date"]).date() if pd.notna(row["min_date"]) else "---"
    max_d = pd.to_datetime(row["max_date"]).date() if pd.notna(row["max_date"]) else "---"
    return f"- *{row['title']}* ({min_d} → {max_d})"

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
        
def parse_date(s):
    return pd.to_datetime(s.strip(), format="%Y-%m-%d", errors="coerce")
    
def short_message(free_tickets, ticket_summary):
    if free_tickets==0:
        return 'всі квитки розпродані'
    else:
        ticket_details = "\n".join(
                [f"- {format_ticket_count(c)} по {p} грн" for p, c in sorted(ticket_summary.items())]
        )
        tickets_msg = f'доступно місць {free_tickets}:\n{ticket_details}'
        return tickets_msg


def full_message(title, link, weekday, event_datetime, free_tickets, tickets_summary):
    event_date_str = event_datetime.strftime("%d.%m.%Y %H:%M")
    event_date_str = f"{normalize_weekday(weekday)}, {event_date_str}"

    title_part = f'\n[{title}]({link}) *{event_date_str}*'
    short_msg = short_message(free_tickets, tickets_summary)
    return f'{title_part} — {short_msg}.\n'
