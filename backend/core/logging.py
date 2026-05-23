import logging
from logging.handlers import RotatingFileHandler

from core.config import settings

_LOGGING_CONFIGURED = False


def configure_logging():
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return

    log_dir = settings.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    )

    llm_handler = RotatingFileHandler(
        log_dir / "llm.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    llm_handler.setFormatter(formatter)
    llm_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    llm_logger = logging.getLogger("knowbase.llm")
    llm_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    llm_logger.addHandler(llm_handler)
    llm_logger.propagate = True

    app_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    app_handler.setFormatter(formatter)
    app_handler.setLevel(logging.INFO)

    app_logger = logging.getLogger("knowbase")
    app_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    app_logger.addHandler(app_handler)

    _LOGGING_CONFIGURED = True
