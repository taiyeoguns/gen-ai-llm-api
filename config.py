from functools import lru_cache
from logging.config import dictConfig
from pathlib import Path
from typing import Any

from decouple import config
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path.cwd()

LOG_LEVEL = config("LOG_LEVEL", default="debug").upper()
LOG_DIR = BASE_DIR / "logs"
PROMPT_TEMPLATES_DIR = BASE_DIR / "app/common/prompt_templates"


dictConfig(
    dict(
        version=1,
        formatters={
            "default": {
                "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s"
            },
            "rich": {"datefmt": "[%X]"},
        },
        handlers={
            "console": {
                "class": "rich.logging.RichHandler",
                "formatter": "rich",
                "level": "DEBUG",
                "rich_tracebacks": True,
            },
            "file": {
                "level": "DEBUG",
                "formatter": "default",
                "class": "logging.handlers.TimedRotatingFileHandler",
                "filename": LOG_DIR / "app.log",
                "when": "D",
                "interval": 1,
                "backupCount": 7,
            },
        },
        root={"handlers": ["console"], "level": "DEBUG"},
        loggers={
            "app": {
                "level": LOG_LEVEL,
                "handlers": ["console", "file"],
                "propagate": False,
            }
        },
    )
)


class Config(BaseSettings):
    VERSION: str = Field(default="v1", json_schema_extra=dict(env="VERSION"))
    DEBUG: bool = Field(default=False, json_schema_extra=dict(env="DEBUG"))

    POSTGRES_USER: str = Field(default="", json_schema_extra=dict(env="POSTGRES_USER"))
    POSTGRES_PASSWORD: str = Field(
        default="", json_schema_extra=dict(env="POSTGRES_PASSWORD")
    )
    POSTGRES_HOST: str = Field(default="", json_schema_extra=dict(env="POSTGRES_HOST"))
    POSTGRES_PORT: str = Field(default="", json_schema_extra=dict(env="POSTGRES_PORT"))
    POSTGRES_DB: str = Field(default="", json_schema_extra=dict(env="POSTGRES_DB"))
    OLLAMA_DOMAIN: str = Field(
        default="localhost", json_schema_extra=dict(env="OLLAMA_DOMAIN")
    )
    OLLAMA_PORT: str = Field(default="11434", json_schema_extra=dict(env="OLLAMA_PORT"))
    OLLAMA_GENERATION_MODEL: str = Field(
        default="", json_schema_extra=dict(env="OLLAMA_GENERATION_MODEL")
    )
    OLLAMA_EMBEDDING_MODEL: str = Field(
        default="", json_schema_extra=dict(env="OLLAMA_EMBEDDING_MODEL")
    )

    DATABASE_URL: str | None = None
    OLLAMA_HOST: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    def build_db_connection(cls, v: str | None, values: dict[str, Any]) -> Any:
        if v:
            return v

        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=values.data.get("POSTGRES_USER"),
                password=values.data.get("POSTGRES_PASSWORD"),
                host=values.data.get("POSTGRES_HOST"),
                port=int(values.data.get("POSTGRES_PORT")),
                path=f"{values.data.get('POSTGRES_DB') or ''}",
            )
        )

    @field_validator("OLLAMA_HOST", mode="before")
    def build_ollama_host(cls, v: str | None, values: dict[str, Any]) -> Any:
        if v:
            return v

        return f"http://{values.data.get('OLLAMA_DOMAIN')}:{values.data.get('OLLAMA_PORT')}"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_config():
    return Config()


CONFIG = get_config()
