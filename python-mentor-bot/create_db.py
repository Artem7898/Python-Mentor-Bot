"""Initialize a SQLite database using the same schema as the Telegram bot."""

import argparse
import asyncio
from pathlib import Path

from bot.config import DEFAULT_DATABASE_PATH
from bot.storage import DatabaseManager


def main() -> None:
    """Create or migrate the database at the requested path."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_DATABASE_PATH)
    args = parser.parse_args()
    asyncio.run(DatabaseManager(args.path).init_db())


if __name__ == "__main__":
    main()
