# Python Mentor Bot

Python Mentor Bot помогает изучать Python в Telegram. Команда `/start` открывает **DASHBOARD**, где можно выбрать урок, посмотреть примеры, задать вопрос, проверить прогресс или сменить язык интерфейса.

[English](README.md) · [Español](README-es.md) · [Документация](docs/README.md)

## Быстрый старт

Понадобятся Python 3.14+, SQLite 3.35+ и токен тестового бота. [@BotFather](https://t.me/BotFather)

Выполните команды из корня репозитория.

```bash
python3.14 -m venv python-mentor-bot/.venv
python-mentor-bot/.venv/bin/python -m pip install -r python-mentor-bot/requirements.txt
```

Задайте `BOT_TOKEN` в окружении процесса или приватном файле `python-mentor-bot/.env`. Запустите бота из каталога приложения.

```bash
(cd python-mentor-bot && .venv/bin/python main.py)
```

Откройте бота в Telegram и отправьте `/start`. Кнопка выбора языка и команда `/language` позволяют переключаться между английским, русским и испанским. Бот сохраняет выбранный язык и прогресс в SQLite.

В программе есть основы Python и отдельные главы по Django, FastAPI, Django REST Framework и Pydantic. Команда `/run (2 + 3) ** 2` вычисляет арифметическое выражение в заданных пределах.

Команды для Windows, конфигурацию, архитектуру, программу занятий и проверки описывает полное руководство. [Документация на русском](docs/ru/README.md)
