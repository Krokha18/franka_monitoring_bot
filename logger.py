import logging

def init_logger():
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
