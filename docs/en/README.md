# Python Mentor Bot guide

[Русский](../ru/README.md) · [Español](../es/README.md) · [Repository overview](../../README.md)

## What the bot does

Open a private chat with the bot and send `/start`. The Telegram **Dashboard** gives you access to the curriculum, code examples, Python installation, questions, progress, and settings.

Open the language picker from the Dashboard or use `/language`. Your choice of English, Russian, or Spanish is saved per Telegram account and survives a restart. Until you choose, the bot uses your supported Telegram language, with Russian as the fallback. Progress is shared across languages.

| Command | Action |
| --- | --- |
| `/start` | Open the Dashboard. |
| `/help` | Show commands and usage. |
| `/language` | Choose the bot language. |
| `/cancel` | Exit the current question dialogue. |
| `/ask` | Ask a Python question in a private chat. |
| `/questions` | View your submitted questions and replies in a private chat. |
| `/pro` | Start an eligible free trial, see the Pro price, or manage your subscription. |
| `/review` | Get a static review of a Python snippet with Pro. |
| `/interview` | Practice Python interview questions with Pro. |
| `/paysupport` | Find help with payments, renewals, and refunds. |
| `/privacy` | Review stored data and request deletion in a private chat. |
| `/run (2 + 3) ** 2` | Evaluate the expression and return `25`. |

The expression evaluator supports integers and finite real numbers with `+ - * / // % **`. It limits input length, tree size, nesting, exponents, and numeric magnitude. Its grammar excludes names, calls, attributes, imports, and statements.

### Free and Pro

Free includes the full curriculum and complete answers to Python questions. The bot checks its built-in answers first. A Free answer can end with a short invitation to try Pro. Pro adds interview practice and static code review, which inspects Python snippets without running them.

If your account is on Free and has never used the trial, open `/pro` in a private chat or choose Pro from the Dashboard, then tap **Start 3-month free trial**. The trial gives you full Pro access for three calendar months at zero cost. The bot shows the expiry in UTC. If the end month has no matching day, the trial ends on its last day.

The trial expires automatically and your account returns to Free. During the trial, `/pro` shows the paid price and keeps purchasing unavailable. After the trial, if sales are enabled, you can start a paid subscription by confirming a Telegram invoice.

New paid subscriptions cost 299 Telegram Stars (XTR) every 30 days. Telegram shows the actual cost of buying Stars in your local currency. Use `/pro` to turn off automatic renewal and keep access until the paid period ends. If the bot disabled renewal, you can unlock it from `/pro` and re-enable it in Telegram while the paid subscription is active. For payment questions or refund requests, use `/paysupport`. The operator issues approved refunds in Stars through Telegram. [Telegram Stars payments](https://core.telegram.org/bots/payments-stars)

### Privacy and questions

Group chats can browse the lesson catalog. Use a private chat for your profile, saved progress, settings, questions, and account deletion. The bot links your profile to your Telegram user ID and saves your username, chosen language, learning activity, and submitted questions.

Submit up to five open questions at a time. Keep tokens and personal information out of your questions. Open questions include new questions and those under review. Authorized mentors can mark a question as under review and save an answer in the private mentor panel. Open `/questions` to read a reply or remove a question after confirming. At startup and every hour while running, the bot purges questions older than 90 days, including answered questions.

To delete your profile, progress, bookmarks, completion records, and questions from the bot's database, use `/privacy` in a private chat and confirm the deletion. Manage Telegram chat history separately in Telegram. Operators manage expiry of older backups separately.

Trial, subscription, and payment records are retained separately for access and payment support. The bot keeps the trial claim tied to your Telegram account to enforce one trial per account, even after you delete learning data. Use `/pro` to manage paid renewal.

If the operator enables OpenAI for questions without a built-in answer, the bot asks permission before sending the question. Each consent applies to that question only.

## Install and run

Requirements are Python 3.14 or newer, SQLite 3.35 or newer, and a Telegram bot token. For development, create a dedicated test bot through [@BotFather](https://t.me/BotFather).

Run these commands from the repository root on Linux or macOS.

```bash
python3.14 -m venv python-mentor-bot/.venv
python-mentor-bot/.venv/bin/python -m pip install --require-hashes -r python-mentor-bot/requirements.lock
python-mentor-bot/.venv/bin/python -c 'import sqlite3; print(sqlite3.sqlite_version)'
```

On Windows with PowerShell, run these commands from the repository root.

```powershell
py -3.14 -m venv .\python-mentor-bot\.venv
.\python-mentor-bot\.venv\Scripts\python.exe -m pip install --require-hashes -r .\python-mentor-bot\requirements.lock
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
| `BOT_OWNER_IDS` | Optional comma-separated Telegram user IDs of owners. |
| `BOT_MENTOR_IDS` | Optional comma-separated Telegram user IDs of mentors. |
| `BOT_EDITOR_IDS` | Optional comma-separated Telegram user IDs of editors. |
| `BILLING_ENABLED` | Enable new paid Pro subscriptions. Default is `false`. Eligible accounts can start a trial with sales disabled. |
| `PRO_PRICE_STARS` | Price for new paid subscriptions. The only accepted value is `299`. |
| `BILLING_SUPPORT_URL` | Optional HTTPS payment support link. Configure this link or at least one owner or mentor before enabling billing. |
| `BILLING_TERMS_URL` | Optional HTTPS link to the subscription terms. |
| `MENTOR_OPENAI_API_KEY` | Optional secret for OpenAI answers after per-question consent. |
| `MENTOR_OPENAI_MODEL` | Model for the OpenAI integration. Default is `gpt-4.1-mini`. |
| `LOG_LEVEL` | Application log level. Default is `INFO`. |
| `DEBUG` | Enables debug logging when `LOG_LEVEL` is unset. |
| `HTTPS_PROXY` | Process environment variable for the proxy to the Telegram API, when required. |

The bot needs outbound HTTPS access to `api.telegram.org`. For a restricted cloud environment, allow that hostname and set the token through the environment’s secret settings. A proxy connection error points to the network path or the proxy configuration. An authentication error returned by Telegram points to the bot token. [Telegram Bot API](https://core.telegram.org/bots/api)

### Deploying billing and optional AI

The standard development configuration leaves `BILLING_ENABLED=false`. Before enabling new purchases, configure a staffed support route and verify that `/paysupport` reaches it. With no support URL, the bot directs users to the private question flow for the configured owners or mentors. Review the price and terms, then enable billing on the intended bot and restart polling. Turning off new purchases leaves existing subscriptions available for management.

For an approved refund, use the deployment's authorized access to call Telegram's `refundStarPayment` with the payer's Telegram user ID and the charge ID from the corresponding receipt. The bot reconciles the refund from Telegram's update. Manage renewal separately if the subscription should stop renewing. [Refund method](https://core.telegram.org/bots/api#refundstarpayment)

Supply Telegram and OpenAI credentials through the authorized deployment's secret settings or a private local `.env`. Set `MENTOR_OPENAI_API_KEY` only if you want to offer external answers for questions without a built-in answer. This feature requires outbound HTTPS access to `api.openai.com`. [OpenAI API documentation](https://platform.openai.com/docs/overview)

### Staff access

Use numeric Telegram user IDs for role assignments. An empty list grants that role to nobody. Set only the roles each account needs and restart the polling process after changing the configuration.

Owners and mentors can use `/mentor` in a private chat to review learner questions. Owners and editors can use `/editor` in a private chat for curriculum contribution instructions. Submit curriculum changes in Git for review and CI before deployment. Keep published lesson identifiers stable, update all three translations, and run each changed example with its documented interpreter and dependencies.

## Curriculum

The catalog has 81 lesson pages across 16 topics. Choose a chapter in the Dashboard, follow a learning path, filter by level, or search lesson and chapter titles in a private chat. Each page identifies its level as Beginner, Intermediate, or Professional. Titles, explanations, and instructions follow your selected language. Code samples are shared across languages.

Use the Dashboard to resume the last lesson you opened. In compact mode, the explanation opens first and code examples open separately. Change the mode in settings. Bookmark pages to return to them later. Mark lessons complete and use the short quizzes on selected topics to check your understanding.

| Chapter | Focus |
| --- | --- |
| Python 3.14 | Interpreter checks, template strings, deferred annotations, Zstandard, and interpreter pools. [What's New in Python 3.14](https://docs.python.org/3.14/whatsnew/3.14.html) |
| What's new in Python 3.15 | UTF-8 by default, comprehension unpacking, frozendict, sentinel values, explicit lazy imports, and the profiling package. [What's New in Python 3.15](https://docs.python.org/3.15/whatsnew/3.15.html) |
| Django | Build a project on 5.2 LTS, work with models, forms, permissions, transactions, ORM optimization and ASGI, then try features from 6.0 and 6.1. The upgrade lesson starts from legacy projects on Django 4.1–5.1. [Django release notes](https://docs.djangoproject.com/en/6.1/releases/) |
| FastAPI | Validate typed requests, compose dependencies, manage resources with lifespan, and test authorization, transactions, and outbound HTTP. [FastAPI documentation](https://fastapi.tiangolo.com/) |
| Django REST Framework | Build serializers and viewsets, apply permissions and scoped queries, paginate results, and test authentication, CSRF, and concurrency-sensitive updates. [DRF documentation](https://www.django-rest-framework.org/) |
| Pydantic v2 | Validate fields and batches, model discriminated unions, and serialize public responses. [Pydantic documentation](https://docs.pydantic.dev/latest/) |
| Python practice | Functions, typing, OOP, file I/O, developer tools, data analysis, async tasks and timeouts, and automated testing with unittest and pytest. |

The walkthroughs target Python 3.14 and run examples specific to 3.15 with that interpreter. Python 3.15 became stable on October 9, 2026. Django 5.2 LTS supports Python up to 3.14. For Django examples on Python 3.15, use Django 6.1.3 or a later 6.1 patch. Django 4.1 is covered as a starting point for migration. [Python 3.15 schedule](https://peps.python.org/pep-0790/) · [Django compatibility](https://docs.djangoproject.com/en/6.1/faq/install/#what-python-version-can-i-use-with-django)

Run lesson examples in their own learning projects and install the chapter's dependencies in a separate virtual environment. Django, DRF, FastAPI, and the data science libraries are learning dependencies. Pydantic v2 is also used by the bot.

## Architecture and storage

Python Mentor Bot runs as a single async process with aiogram long polling. `main.py` owns startup, HTTP session, and database lifecycles. `bot/handlers.py` routes commands and callback queries. `bot/i18n.py` resolves and renders the user's interface language. The lesson catalog supplies pages to the handlers. Pydantic v2 validates configuration and persisted records. `bot/storage.py` reuses an aiosqlite connection and binds values in SQL statements.

SQLite retains learner profiles, preferences, progress, bookmarks, completion, and submitted questions. Temporary conversation state, such as waiting for a question, lives in memory and expires. A restart clears that temporary state.

The bot creates its schema on startup. For an older `python_mentor.db` or `bot_data.db`, stop all writers and make a SQLite backup. Point `DATABASE_PATH` to a writable copy of that backup. Schema initialization adds the needed progress or language columns to compatible older databases and preserves existing rows. Questions submitted after migration go into `user_questions`.

You can initialize a database copy without a Telegram token. Substitute the absolute path to the copy and run from the repository root.

```bash
(cd python-mentor-bot && .venv/bin/python create_db.py /absolute/path/to/working.db)
```

Initialization is repeatable. Keep `DATABASE_PATH` and backups outside the repository and in a directory accessible only to the service account and authorized operators. Use a service-owned directory with no shared write access and a regular database file. On POSIX systems, use `0700` for the directory and `0600` for database files and backups. On Windows, restrict access with ACLs. Apply the same policy to SQLite sidecar files. Test restoration on a private copy and expire backups according to your retention policy. [SQLite backup documentation](https://sqlite.org/backup.html)

The historical SQLite file was removed from the current checkout after a restricted local archive was verified. Its earlier Git commits retain the file. The repository history was preserved. Keep repository and backup access restricted until the data owner has reviewed the earlier copies.

## Development checks

Run from the repository root in Bash.

```bash
python-mentor-bot/.venv/bin/python -m pip install --require-hashes -r python-mentor-bot/requirements-dev.lock
(cd python-mentor-bot && .venv/bin/ruff check .)
(cd python-mentor-bot && .venv/bin/ruff format --check .)
(cd python-mentor-bot && .venv/bin/python -B -m pytest -p no:cacheprovider)
```

On PowerShell, enter the application directory, use `.\.venv\Scripts\python.exe` and `.\.venv\Scripts\ruff.exe`, and keep the same Ruff and pytest arguments.

When changing dependencies, regenerate both locks with uv from the application directory.

```bash
uv pip compile --universal --python-version 3.14 --generate-hashes --no-annotate --output-file requirements.lock requirements.txt
uv pip compile --universal --python-version 3.14 --generate-hashes --no-annotate --constraint requirements.lock --output-file requirements-dev.lock requirements-dev.txt
```

CI runs Ruff and pytest on Python 3.14 and 3.15, audits runtime dependencies with pip-audit, scans Git history with redacted Gitleaks output, and rejects tracked deployment databases and dotenv files except the example template. The hash-checked lock files pin runtime and development dependencies. Review and test lock-file updates alongside changes to the dependency manifests.

Automated tests use simulated Telegram updates and temporary databases. For a live smoke check, use a dedicated test bot and open the Dashboard from a private chat. Switch languages, browse a learning path, try compact mode, bookmark and complete a lesson, and answer a short quiz. Restart the bot and check saved progress from two accounts. Submit a question and check access with an authorized mentor and an ordinary account. Verify that a group permits catalog browsing and sends personal actions to a private chat. Confirm deletion with `/privacy` on a test profile.

Use simulated Telegram payment updates and a temporary database to check checkout, activation, renewal, duplicate delivery, cancellation, refunds, and continued access after deleting learning data. Use a dedicated bot with billing disabled for manual trial activation. In automated checks, verify expiry, the return to Free, and rejection of a second trial, including after learning-data deletion.

For an end-to-end payment check without real charges, create a bot in Telegram's dedicated test environment and use a separate SQLite database. Start `main()` with an `AiohttpSession(api=TEST)` from aiogram using `TEST` from `aiogram.client.telegram`. Supply the test token, set `BILLING_ENABLED=true` for that run, and configure the session's proxy if required. [Telegram test environment](https://core.telegram.org/bots/features#dedicated-test-environment)

For changes to handlers or storage, cover stale callbacks, unavailable messages, empty questions, and overlapping updates from one account. For changes to validation, cover absent tokens, redacted errors, invalid expressions, and numeric limits. For changes to lessons or translations, verify chapter navigation, code escaping, and Telegram message length.
