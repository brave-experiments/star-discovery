from __future__ import annotations

import os
from typing import Final, TypeVar

ARG_NAME: Final[str] = "SD_DEBUG"
ARG_VALUE: Final[str] = "1"
CACHE_KEY: Final[str] = "is_debug"

T = TypeVar("T")


__cache: dict[str, bool | None] = {CACHE_KEY: None}


def is_debug() -> bool:
    if __cache[CACHE_KEY] is not None:
        return __cache[CACHE_KEY]
    __cache[CACHE_KEY] = ARG_NAME in os.environ and os.environ[ARG_NAME] == ARG_VALUE
    assert isinstance(__cache[CACHE_KEY], bool)
    return __cache[CACHE_KEY]


def set_debug_mode(debug: bool) -> None:
    os.environ[ARG_NAME] = str(int(debug))
    __cache[CACHE_KEY] = None
