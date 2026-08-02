import logging
from pathlib import Path
import sys
from typing import Any

import star_discovery

LOGGER_NAME = star_discovery.NAME
STDOUT_DESC = "_"
"""String used for denoting when we want to route a message to STDOUT instead
of to a file on disk."""


class Logger:
    _logger: logging.Logger
    _will_log_debug: bool
    _will_log_info: bool
    _will_log_error: bool

    def __init__(self, logger: logging.Logger):
        self._logger = logger
        self._will_log_debug = logger.isEnabledFor(logging.DEBUG)
        self._will_log_info = logger.isEnabledFor(logging.INFO)
        self._will_log_error = logger.isEnabledFor(logging.ERROR)

    def debug(self, msg: Any, *args: Any) -> None:
        return self._logger.debug(msg, *args)

    def will_log_debug(self) -> bool:
        return self._will_log_debug

    def info(self, msg: Any, *args: Any) -> None:
        return self._logger.info(msg, *args)

    def will_log_info(self) -> bool:
        return self._will_log_info

    def error(self, msg: Any, *args: Any) -> None:
        return self._logger.error(msg, *args)

    def will_log_error(self) -> bool:
        return self._will_log_error


def get_logger() -> Logger:
    base_logger = logging.getLogger(LOGGER_NAME)
    return Logger(base_logger)


def config(logging_dest: str, level: logging._Level | None) -> Logger:
    output_handler: logging.Handler | None = None
    if not level:
        output_handler = logging.NullHandler()
    elif logging_dest == STDOUT_DESC:
        output_handler = logging.StreamHandler(sys.stdout)
    else:
        log_path = Path(logging_dest)
        # Trigger an error as soon as possible if we're given an invalid
        # path to try and write a log to.
        log_path.touch(exist_ok=True)
        output_handler = logging.FileHandler(log_path, encoding="utf8")
    output_handler.setLevel(logging.DEBUG)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)

    base_logger = logging.getLogger(LOGGER_NAME)
    base_logger.addHandler(output_handler)
    base_logger.addHandler(error_handler)
    return Logger(base_logger)
