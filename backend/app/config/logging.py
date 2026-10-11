import inspect
import logging
import sys

from loguru import logger

from app.config.settings import LogSettings


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = inspect.currentframe(), 0
        while frame is not None and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(settings: LogSettings) -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.level)
    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
