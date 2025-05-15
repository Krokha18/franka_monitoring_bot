# Theater Ticket Monitoring Bot

This bot monitors ticket availability for selected performances at the Franko Theater. It checks ticket availability on the theater's website and sends updates to a specified Telegram chat if new tickets become available.

## Features
- Periodically checks ticket availability for selected performances.
- Sends Telegram notifications when new tickets are found.
- Stores ticket data locally to avoid duplicate notifications.
- Configurable monitoring titles.
- Integrated with `systemd` for deployment as a service.

## Requirements
- Python 3.10+
- Required Python packages:
  - `selenium`
  - `telebot`
  - `systemd-python`
  - `python-dotenv`

Install APT-packages with:
```bash
sudo apt-get update
sudo apt-get install -y \
    wget curl unzip gnupg pkg-config libsystemd-dev build-essential \
    chromium chromium-driver
sudo rm -rf /var/lib/apt/lists/*
```

Activate virtual environment (optional):
```bash
python3.11 -m venv venv
source venv/bin/activate
```

Install Python requirements with:
```bash
pip install -r requirements.txt
```

## Configuration
1. **Set the Telegram Bot Token and Chat ID:**
   Make sure that environment variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_GROUP_ID` are set in .env file.

2. **Set Monitoring Titles:**
   Add the titles (in UPPER style) of performances to the `monitoring_titles.json` list, for example:
   ```json
   [
    "ТАРТЮФ",
    "КОНОТОПСЬКА ВІДЬМА",
    "БЕЗТАЛАННА",
    "КАЛІГУЛА"
   ]
   ```

3. **Set Database File Path:**
   The script uses `event_tickets_db.json` for storing ticket availability data. Ensure the script has write permissions for this file.

## Running as a Systemd Service

To run the bot as a `systemd` service:

1. **Create a Systemd Service File:**
   Create a file `/etc/systemd/system/franka_bot.service` with the following content:
   ```ini
   [Unit]
   Description=Franka Theater Ticket Monitoring Bot
   After=network.target

   [Service]
   ExecStart=/usr/bin/python3 /path/to/franka_bot.py
   WorkingDirectory=/path/to
   Environment="PYTHONUNBUFFERED=1"
   StandardOutput=journal
   StandardError=journal
   Restart=always
   RestartSec=300

   [Install]
   WantedBy=multi-user.target
   ```
   Also, create a file `/etc/systemd/system/franka_bot_commands.service` for bot commands handler:
   ```ini
   # /etc/systemd/system/bot_commands.service
   [Unit]
   Description=Telegram Bot Commands Listener
   After=network.target

   [Service]
   ExecStart=/path/to/python3 /path/to/franka_monitoring_bot/bot_commands.py
   WorkingDirectory=/path/to/franka_monitoring_bot
   Restart=always
   Environment="PYTHONUNBUFFERED=1"

   [Install]
   WantedBy=multi-user.target
   ```
   

2. **Reload Systemd and Start the Service:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable franka_bot.service franka_bot_commands.service
   sudo systemctl start franka_bot.service franka_bot_commands.service
   ```

3. **Monitor the Logs:**
   View the bot's logs with:
   ```bash
   journalctl -u franka_bot.service -f
   ```

## Usage
- The bot checks ticket availability every 5 minutes (configurable in `RestartSec` in the service file).
- If new tickets are found, a notification is sent to the specified Telegram chat.

## Contributions
Feel free to open issues or submit pull requests to improve this bot.

## License
This project is licensed under the MIT License.

