# Python Mentor Bot guide

[Русский](../ru/README.md) · [Español](../es/README.md) · [Repository overview](../../README.md)

## What the bot does

Open a private chat with the bot and send `/start`. **DASHBOARD** is an inline Telegram menu with shortcuts to the curriculum, code examples, Python installation, questions, progress, and language settings. Your Telegram account identifies your profile automatically.

Open the language picker from DASHBOARD or use `/language`. Select English, Russian, or Spanish. Your selection is saved per Telegram account and survives a restart. Until you choose a language, the bot uses your Telegram language if supported and falls back to Russian otherwise. Progress is shared across languages.

| Command | Action |
| --- | --- |
| `/start` | Open DASHBOARD. |
| `/help` | Show commands and usage. |
| `/language` | Choose the bot language. |
| `/cancel` | Exit the current question dialogue. |
| `/run (2 + 3) ** 2` | Evaluate the expression and return `25`. |

The bot saves questions for review and confirms receipt. The expression evaluator supports finite integers and real numbers with `+ - * / // % **`. It limits input length, tree size, nesting, exponents, and numeric magnitude. Its grammar excludes names, calls, attributes, imports, and statements.

## Install and run

Requirements are Python 3.14 or newer, SQLite 3.35 or newer, and a Telegram bot token. For development, create a dedicated test bot through [@BotFather](https://t.me/BotFather).

Run these commands from the repository root on Linux or macOS.

```bash
python3.14 -m venv python-mentor-bot/.venv
python-mentor-bot/.venv/bin/python -m pip install -r python-mentor-bot/requirements.txt
python-mentor-bot/.venv/bin/python -c 'import sqlite3; print(sqlite3.sqlite_version)'
```

On Windows with PowerShell, run these commands from the repository root.

```powershell
py -3.14 -m venv .\python-mentor-bot\.venv
.\python-mentor-bot\.venv\Scripts\python.exe -m pip install -r .\python-mentor-bot\requirements.txt
.\python-mentor-bot\.venv\Scripts\python.exe -c "import sqlite3; print(sqlite3.sqlite_version)"
```

Set `BOT_TOKEN` in the process environment or in a private `python-mentor-bot/.env` file. Replace the placeholder with your test token and keep it out of Git and logs.

```dotenv
BOT_TOKEN=replace_with_your_test_bot_token
```

Start the bot from the application directory. In Bash, run this command from the repository root.

```bash
(cd python-mentor-bot && .venv/bin/python main.py)
```

In PowerShell, run these commands from the repository root.

```powershell
Push-Location .\python-mentor-bot
.\.venv\Scripts\python.exe main.py
Pop-Location
```

Wait for aiogram to report `Run polling`, then send the bot `/start`. Run a single polling process per token. If Telegram reports a polling conflict, stop the previous instance and check for an existing webhook before restarting.

### Configuration

Process environment values take precedence over settings in `.env`. Relative paths resolve from the application's working directory.

| Setting | Purpose |
| --- | --- |
| `BOT_TOKEN` | Required BotFather token. Malformed tokens are rejected at startup. |
| `DATABASE_PATH` | Path to the writable SQLite database. Default is `data/python_mentor.db`. |
| `LOG_LEVEL` | Application log level. Default is `INFO`. |
| `DEBUG` | Enables debug logging when `LOG_LEVEL` is unset. |
| `HTTPS_PROXY` | Process environment variable for the proxy to the Telegram API, when required. |

The bot needs outbound HTTPS access to `api.telegram.org`. For a restricted cloud environment, allow that hostname and set the token through the environment’s secret settings. A proxy connection error points to the network path or the proxy configuration. An authentication error returned by Telegram points to the bot token. [Telegram Bot API](https://core.telegram.org/bots/api)

## Curriculum

The curriculum includes Python basics, modern syntax, object-oriented programming, files, developer tools, data science, and asynchronous I/O. Open a chapter from DASHBOARD to read pages or open its code examples.

| Chapter | Focus |
| --- | --- |
| Django | Project and application structure, models, migrations, and the request/response flow. [Django documentation](https://docs.djangoproject.com/) |
| FastAPI | Typed API endpoints, request validation, and generated OpenAPI documentation. [FastAPI documentation](https://fastapi.tiangolo.com/) |
| Django REST Framework | Serializers and REST endpoints backed by Django models. [Django REST Framework documentation](https://www.django-rest-framework.org/) |
| Pydantic | Data models, field constraints, validation, and serialization. [Pydantic documentation](https://docs.pydantic.dev/latest/) |

Lesson snippets are examples to run in separate learning projects. Follow their chapter-specific dependency instructions in a separate virtual environment. Django, Django REST Framework, FastAPI, and Uvicorn are optional learning dependencies. Pydantic v2 is a bot dependency as well as a course subject.

## Architecture and storage

Python Mentor Bot runs as a single async process with aiogram long polling. `main.py` owns startup, HTTP session, and database lifecycles. `bot/handlers.py` routes commands and callback queries. `bot/i18n.py` resolves and renders the user's interface language. The lesson catalog supplies pages to the handlers. Pydantic v2 validates configuration and persisted records. `bot/storage.py` reuses an aiosqlite connection and binds values in SQL statements.

SQLite retains registration, selected language, current chapter and page, and submitted questions. Temporary conversation state, such as waiting for a question, lives in memory and expires. A restart clears that temporary state.

The bot creates its schema on startup. For an older `python_mentor.db` or `bot_data.db`, stop all writers and make a SQLite backup. Point `DATABASE_PATH` to a writable copy of that backup. Schema initialization adds the needed progress or language columns to compatible older databases and preserves existing rows. Questions submitted after migration go into `user_questions`.

You can initialize a database copy without a Telegram token. Substitute the absolute path to the copy and run from the repository root.

```bash
(cd python-mentor-bot && .venv/bin/python create_db.py /absolute/path/to/working.db)
```

Initialization is repeatable. Keep backups and database files private because they contain Telegram identifiers, usernames, and submitted questions. [SQLite backup documentation](https://sqlite.org/backup.html)

## Development checks

Run from the repository root in Bash.

```bash
python-mentor-bot/.venv/bin/python -m pip install -r python-mentor-bot/requirements-dev.txt
(cd python-mentor-bot && .venv/bin/ruff check .)
(cd python-mentor-bot && .venv/bin/ruff format --check .)
(cd python-mentor-bot && .venv/bin/python -B -m pytest -p no:cacheprovider)
```

On PowerShell, enter the application directory, use `.\.venv\Scripts\python.exe` and `.\.venv\Scripts\ruff.exe`, and keep the same Ruff and pytest arguments.

Automated tests use simulated Telegram updates and temporary databases. For a live smoke check with a test bot, open DASHBOARD, switch to each language, and open a framework lesson. Record progress on a lesson page, send a question, and evaluate `/run 2 ** 3`. Restart the bot and verify the language and progress persist. Use a second account to verify those preferences are independent.

For changes to handlers or storage, cover stale callbacks, unavailable messages, empty questions, and overlapping updates from one account. For changes to validation, cover absent tokens, redacted errors, invalid expressions, and numeric limits. For changes to lessons or translations, verify chapter navigation, code escaping, and Telegram message length.
