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