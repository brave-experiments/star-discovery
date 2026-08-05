import logging
from pathlib import Path
import sys
from typing import Any

import star_discovery

LEVELS = ["debug", "info", "quiet"]
DEFAULT_LEVEL = "info"
LEVEL_MAP: dict[str, logging._Level | None] = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "quiet": None,
}
LOGGER_NAME = star_discovery.NAME
STDOUT_DESC = Path("-")
"""String used for denoting when we want to route a message to STDOUT instead
of to a file on disk."""


class Logger:
    _logger: logging.Logger
    _will_log_debug: bool
    _will_log_info: bool
    _level_name: str

    def __init__(self, level: logging._Level | None, logger: logging.Logger):
        self._logger = logger
        if level == logging.DEBUG:
            self._level_name = LEVELS[0]
            self._will_log_debug = True
            self._will_log_info = True
        elif level == logging.INFO:
            self._level_name = LEVELS[1]
            self._will_log_debug = False
            self._will_log_info = True
        else:
            self._level_name = LEVELS[2]
            self._will_log_debug = False
            self._will_log_info = False

    def level(self) -> str:
        return self._level_name

    def debug(self, msg: Any, *args: Any) -> None:
        if self._will_log_debug:
            self._logger.debug(msg, *args)

    def will_log_debug(self) -> bool:
        return self._will_log_debug

    def info(self, msg: Any, *args: Any) -> None:
        if self._will_log_info:
            self._logger.info(msg, *args)

    def will_log_info(self) -> bool:
        return self._will_log_info

    def error(self, msg: Any, *args: Any) -> None:
        return self._logger.error(msg, *args)


def config(level: str) -> Logger:
    try:
        base_logger = logging.getLogger(LOGGER_NAME)
        logging_level = LEVEL_MAP[level]
        logging.basicConfig(level=logging_level, stream=sys.stdout)
        return Logger(logging_level, base_logger)
    except KeyError:
        # pylint: disable-next=raise-missing-from
        raise ValueError(f"Invalid logging level: {level}")
