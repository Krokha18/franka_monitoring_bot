#!/bin/bash

set -e  # зупинити скрипт при помилці

# У dev-середовищі активувати venv
if [[ -f "venv/bin/activate" && ! -f "/.dockerenv" ]]; then
    echo "Activating virtualenv..."
    source venv/bin/activate
fi

# Пастка на завершення — вбити всю групу процесів
trap 'echo "Stopping all child processes..."; kill -- -$$; exit' SIGINT SIGTERM

# Запускаємо командний бот (основний процес)
#python bot_commands.py &

# Периодичний запуск franka_bot.py кожні 30 сек
(
  while true; do
    python franka_bot.py
    sleep 30
  done
) &

# Периодичний запуск update_event_list.py кожні 10 хв
(
  while true; do
    python update_event_list.py
    sleep 600
  done
) &

# Чекаємо завершення всіх дочірніх процесів
wait
