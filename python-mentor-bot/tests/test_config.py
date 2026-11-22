"""Verify source precedence, validated settings, and token redaction."""

from pathlib import Path

import pytest

from bot.config import Config, ConfigError


def test_environment_overrides_dotenv(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "BOT_TOKEN=1234:file-test\n"
        "DATABASE_PATH=local.db\n"
        "LOG_LEVEL=warnING\n"
        "UNRELATED_FILE_KEY=ignored\n",
        encoding="utf-8",
    )
    token = "5678:environment-test"
    settings = Config.load(env_file, environ={"BOT_TOKEN": token})

    assert settings.bot_token.get_secret_value() == token
    assert settings.database_path == Path("local.db")
    assert settings.log_level == "WARNING"
    assert token not in repr(settings)
    assert token not in settings.model_dump_json()


def test_environment_can_explicitly_clear_dotenv_value() -> None:
    with pytest.raises(ConfigError, match="BOT_TOKEN"):
        Config.from_sources({"BOT_TOKEN": "1234:file-test"}, environ={"BOT_TOKEN": ""})


def test_default_database_path_is_outside_tracked_database() -> None:
    settings = Config.from_sources({"BOT_TOKEN": "1234:sample"}, environ={})
    assert settings.database_path == Path("data/python_mentor.db")


def test_invalid_token_error_omits_secret() -> None:
    invalid = "invalid-credential-material"
    with pytest.raises(ConfigError, match="BOT_TOKEN") as exc:
        Config.from_sources({"BOT_TOKEN": invalid}, environ={})
    assert invalid not in str(exc.value)


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        pytest.param({"DEBUG": "true"}, "DEBUG", id="debug-enabled"),
        pytest.param({"DEBUG": "false"}, "INFO", id="debug-disabled"),
        pytest.param({"DEBUG": "true", "LOG_LEVEL": "ERROR"}, "ERROR", id="explicit-log-level"),
    ],
)
def test_log_level(values: dict[str, str], expected: str) -> None:
    settings = Config.from_sources({"BOT_TOKEN": "1234:sample", **values}, environ={})
    assert settings.log_level == expected


@pytest.mark.parametrize(
    ("key", "value"),
    [("DATABASE_PATH", ""), ("DATABASE_PATH", "broken\x00path"), ("LOG_LEVEL", "loud")],
)
def test_invalid_setting(key: str, value: str) -> None:
    with pytest.raises(ConfigError, match=key):
        Config.from_sources({"BOT_TOKEN": "1234:sample", key: value}, environ={})


def test_roles_are_empty_by_default() -> None:
    settings = Config.from_sources({"BOT_TOKEN": "1234:sample"}, environ={})
    assert settings.owner_ids == settings.mentor_ids == settings.editor_ids == frozenset()


def test_roles_parse_independently_and_environment_can_clear_file_values() -> None:
    settings = Config.from_sources(
        {
            "BOT_TOKEN": "1234:sample",
            "BOT_OWNER_IDS": " 12345 , 23456,12345 ",
            "BOT_MENTOR_IDS": "34567",
            "BOT_EDITOR_IDS": "45678",
        },
        environ={"BOT_MENTOR_IDS": " ", "BOT_EDITOR_IDS": "56789"},
    )
    assert settings.owner_ids == frozenset({12345, 23456})
    assert settings.mentor_ids == frozenset()
    assert settings.editor_ids == frozenset({56789})


@pytest.mark.parametrize(
    "invalid",
    [
        "0",
        "123,0",
        "123,,234",
        "123,",
        "-123",
        "+123",
        "\uff11\uff12\uff13",
        "9223372036854775808",
    ],
)
def test_roles_reject_invalid_telegram_ids(invalid: str) -> None:
    with pytest.raises(ConfigError, match="BOT_OWNER_IDS"):
        Config.from_sources({"BOT_TOKEN": "1234:sample", "BOT_OWNER_IDS": invalid}, environ={})
