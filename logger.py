import logging

def init_logger():
    logger = logging.getLogger()
    if logger.handlers:
        return  # Уникаємо дублювання хендлерів

    try:
        import systemd.journal
        journal_handler = systemd.journal.JournalHandler()
        journal_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(journal_handler)
        logger.setLevel(logging.INFO)
    except ImportError:
        logging.basicConfig(
            filename='bot.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

