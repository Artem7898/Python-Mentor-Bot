"""Validated application settings from the environment and an optional .env file."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Annotated, Final, Literal, Self

from dotenv import dotenv_values
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
    ValidationError,
    field_validator,
    model_validator,
)

type LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
type TelegramId = Annotated[int, Field(gt=0, le=2**63 - 1)]

DEFAULT_DATABASE_PATH = Path("data/python_mentor.db")
PRO_PRICE_STARS: Final = 299

_TOKEN_PATTERN = re.compile(r"[1-9][0-9]{0,19}:[A-Za-z0-9_-]+")
_MODEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}")
_TRUE_VALUES = frozenset({"1", "true", "on", "yes"})
_FALSE_VALUES = frozenset({"0", "false", "off", "no"})
_SETTINGS_KEYS = (
    "BOT_TOKEN",
    "DATABASE_PATH",
    "LOG_LEVEL",
    "DEBUG",
    "BOT_OWNER_IDS",
    "BOT_MENTOR_IDS",
    "BOT_EDITOR_IDS",
    "BILLING_ENABLED",
    "PRO_PRICE_STARS",
    "BILLING_SUPPORT_URL",
    "BILLING_TERMS_URL",
    "MENTOR_OPENAI_API_KEY",
    "MENTOR_OPENAI_MODEL",
)


class ConfigError(ValueError):
    """A startup setting is absent, unreadable, or invalid."""


class Config(BaseModel):
    """Read-only configuration for the Telegram client and SQLite storage."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
        strict=True,
        validate_by_name=True,
        validate_by_alias=True,
    )

    bot_token: Annotated[
        SecretStr, Field(validation_alias="BOT_TOKEN", repr=False, min_length=3, max_length=256)
    ]
    database_path: Annotated[Path, Field(validation_alias="DATABASE_PATH")] = DEFAULT_DATABASE_PATH
    log_level: Annotated[LogLevel, Field(validation_alias="LOG_LEVEL")] = "INFO"
    owner_ids: Annotated[frozenset[TelegramId], Field(validation_alias="BOT_OWNER_IDS")] = (
        frozenset()
    )
    mentor_ids: Annotated[frozenset[TelegramId], Field(validation_alias="BOT_MENTOR_IDS")] = (
        frozenset()
    )
    editor_ids: Annotated[frozenset[TelegramId], Field(validation_alias="BOT_EDITOR_IDS")] = (
        frozenset()
    )
    billing_enabled: Annotated[bool, Field(validation_alias="BILLING_ENABLED")] = False
    pro_price_stars: Annotated[Literal[299], Field(validation_alias="PRO_PRICE_STARS")] = (
        PRO_PRICE_STARS
    )
    billing_support_url: Annotated[
        HttpUrl | None, Field(validation_alias="BILLING_SUPPORT_URL")
    ] = None
    billing_terms_url: Annotated[HttpUrl | None, Field(validation_alias="BILLING_TERMS_URL")] = None
    mentor_openai_api_key: Annotated[
        SecretStr | None, Field(validation_alias="MENTOR_OPENAI_API_KEY", repr=False)
    ] = None
    mentor_openai_model: Annotated[str, Field(validation_alias="MENTOR_OPENAI_MODEL")] = (
        "gpt-4.1-mini"
    )

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, value: SecretStr) -> SecretStr:
        """Reject malformed token syntax before making a Telegram request."""
        if not _TOKEN_PATTERN.fullmatch(value.get_secret_value()):
            raise ValueError("expected a Telegram bot token from BotFather")
        return value

    @field_validator("database_path", mode="before")
    @classmethod
    def parse_database_path(cls, value: object) -> Path:
        """Normalize the file path without performing filesystem I/O."""
        if isinstance(value, Path):
            value = str(value)
        if not isinstance(value, str) or not value.strip() or "\x00" in value:
            raise ValueError("expected a nonempty SQLite path without NUL bytes")
        return Path(value)

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        """Permit case-insensitive logging levels in environment variables."""
        return value.strip().upper() if isinstance(value, str) else value

    @field_validator("owner_ids", "mentor_ids", "editor_ids", mode="before")
    @classmethod
    def parse_role_ids(cls, value: object) -> frozenset[TelegramId]:
        """Parse comma-separated positive Telegram account IDs."""
        if isinstance(value, frozenset):
            return value
        if not isinstance(value, str):
            raise ValueError("expected a comma-separated list of Telegram user IDs")
        if not value.strip():
            return frozenset()

        identifiers = tuple(item.strip() for item in value.split(","))
        if any(
            len(identifier) > 19 or not identifier.isascii() or not identifier.isdecimal()
            for identifier in identifiers
        ):
            raise ValueError("expected a comma-separated list of decimal Telegram user IDs")
        return frozenset(map(int, identifiers))

    @field_validator("billing_enabled", mode="before")
    @classmethod
    def parse_billing_enabled(cls, value: object) -> object:
        """Parse an explicit environment opt-in for new purchases."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in _TRUE_VALUES:
                return True
            if normalized in _FALSE_VALUES:
                return False
        return value

    @field_validator("pro_price_stars", mode="before")
    @classmethod
    def parse_star_price(cls, value: object) -> object:
        """Accept the project price when supplied via the legacy environment variable."""
        if isinstance(value, str):
            value = value.strip()
            if len(value) <= 5 and value.isascii() and value.isdecimal():
                return int(value)
        return value

    @field_validator("billing_support_url", "billing_terms_url")
    @classmethod
    def validate_billing_url(cls, value: HttpUrl | None) -> HttpUrl | None:
        """Permit HTTPS support and terms links without embedded credentials."""
        if value is not None and (
            value.scheme != "https" or value.username is not None or value.password is not None
        ):
            raise ValueError("expected an HTTPS URL without embedded credentials")
        return value

    @field_validator("mentor_openai_api_key")
    @classmethod
    def validate_mentor_api_key(cls, value: SecretStr | None) -> SecretStr | None:
        """Reject unusable key values without including them in diagnostics."""
        if value is not None:
            key = value.get_secret_value()
            if not key or any(char.isspace() for char in key):
                raise ValueError("expected a nonempty API key without whitespace")
        return value

    @field_validator("mentor_openai_model")
    @classmethod
    def validate_mentor_model(cls, value: str) -> str:
        """Require a single model identifier."""
        if not _MODEL_PATTERN.fullmatch(value):
            raise ValueError("expected a valid model identifier")
        return value

    @model_validator(mode="after")
    def validate_billing_support(self) -> Self:
        """Ensure buyers have a reachable support route before selling."""
        if self.billing_enabled and not (
            self.billing_support_url or self.owner_ids or self.mentor_ids
        ):
            raise ValueError("BILLING_ENABLED requires BILLING_SUPPORT_URL or a support operator")
        return self

    @classmethod
    def load(
        cls,
        env_file: str | Path = ".env",
        *,
        environ: Mapping[str, str] | None = None,
    ) -> Self:
        """Read the selected dotenv file and apply environment overrides."""
        try:
            file_values = dotenv_values(env_file)
        except OSError, UnicodeError:
            raise ConfigError("Could not read the dotenv configuration file") from None
        return cls.from_sources(file_values, environ=environ)

    @classmethod
    def from_sources(
        cls,
        file_values: Mapping[str, str | None],
        *,
        environ: Mapping[str, str] | None = None,
    ) -> Self:
        """Validate known keys, letting process variables override file values.

        Raises:
            ConfigError: A setting is missing or invalid. Diagnostics omit inputs.
        """
        source = os.environ if environ is None else environ
        values = {
            key: value for key in _SETTINGS_KEYS if (value := file_values.get(key)) is not None
        }
        values.update({key: source[key] for key in _SETTINGS_KEYS if key in source})

        debug = values.pop("DEBUG", None)
        if debug is not None:
            normalized = debug.strip().lower()
            if normalized in _TRUE_VALUES:
                values.setdefault("LOG_LEVEL", "DEBUG")
            elif normalized not in _FALSE_VALUES:
                raise ConfigError("DEBUG must be a boolean")

        try:
            return cls.model_validate(values)
        except ValidationError as exc:
            errors = exc.errors(include_input=False, include_context=False, include_url=False)
            details = "\n".join(
                f"{'.'.join(map(str, error['loc']))}: {error['msg']}" for error in errors
            )
            raise ConfigError(details) from None
