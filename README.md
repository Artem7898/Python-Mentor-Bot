# Python Mentor Bot

Python Mentor Bot teaches Python inside Telegram. Open **DASHBOARD** with `/start` to browse lessons, view code examples, ask a question, check your progress, or change the interface language.

[Русский](README-ru.md) · [Español](README-es.md) · [Documentation](docs/README.md)

## Video demo

[Watch Python Mentor Bot in action on YouTube](https://youtu.be/Bespied313c?si=DRmlSorw1F7Is1yg)

## Quick start

You need Python 3.14+, SQLite 3.35+, and a test bot token. [@BotFather](https://t.me/BotFather)

From the repository root, create an environment and install the bot dependencies.

```bash
python3.14 -m venv python-mentor-bot/.venv
python-mentor-bot/.venv/bin/python -m pip install -r python-mentor-bot/requirements.txt
```

Set `BOT_TOKEN` in the process environment or a private `python-mentor-bot/.env` file. Start the bot from its application directory.

```bash
(cd python-mentor-bot && .venv/bin/python main.py)
```

Open the bot in Telegram and send `/start`. The language button and `/language` offer English, Russian, and Spanish. The bot saves your selection and progress in SQLite.

The curriculum covers Python fundamentals and separate Django, FastAPI, Django REST Framework, and Pydantic chapters. `/run (2 + 3) ** 2` evaluates a bounded arithmetic expression.

See the full guide for Windows commands, configuration, architecture, curriculum, and tests. [English documentation](docs/en/README.md)
