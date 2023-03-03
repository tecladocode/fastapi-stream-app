import logging
from logging.config import dictConfig

from storeapi.config import config


def obfuscated(email):
    """Obfuscate email address for logging purposes."""
    characters = email[:2]
    first, last = email.split("@")
    return characters + ("*" * (len(first) - 2)) + "@" + last


class EmailObfuscationFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if "email" in record.__dict__:
            record.email = obfuscated(record.email)
        return True


handlers = ["default", "rotating_file"]
if config.ENV_STATE == "prod":
    handlers = ["default", "rotating_file", "logtail"]


def configure_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 8 if config.ENV_STATE == "dev" else 32,
                    "default_value": "-",
                },
                "email_obfuscation": {"()": EmailObfuscationFilter},
            },
            "formatters": {
                "console": {
                    "class": "logging.Formatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    "format": "(%(correlation_id)s) %(name)s:%(lineno)d - %(message)s",
                },
                "file": {
                    "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                    # For JsonFormatter, the format string just defines what keys are included in the log record
                    # It's a bit clunky, but it's the way to do it for now
                    "format": "%(asctime)s %(msecs)03d %(levelname)s %(correlation_id)s %(name)s %(lineno)d %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "class": "rich.logging.RichHandler",  # could use logging.StreamHandler instead
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id", "email_obfuscation"],
                },
                "logtail": {
                    # https://betterstack.com/docs/logs/python/
                    "class": "logtail.LogtailHandler",
                    "level": "DEBUG",
                    "formatter": "console",
                    "filters": ["correlation_id", "email_obfuscation"],
                    "source_token": config.LOGTAIL_API_KEY,  # gets passed to LogtailHandler constructor as kwargs
                },
                "rotating_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "file",
                    "filters": ["correlation_id", "email_obfuscation"],
                    "filename": "storeapi.log",
                    "maxBytes": 1024 * 1024,  # 1 MB
                    "backupCount": 2,
                    "encoding": "utf8",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default", "rotating_file"], "level": "INFO"},
                "storeapi": {
                    "handlers": handlers,
                    "level": "DEBUG" if config.ENV_STATE == "dev" else "INFO",
                    "propagate": False,
                },
                "databases": {"handlers": ["default"], "level": "WARNING"},
                "aiosqlite": {"handlers": ["default"], "level": "WARNING"},
            },
        }
    )
