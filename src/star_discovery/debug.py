from __future__ import annotations

import os

ARG_NAME = "SD_DEBUG"
ARG_VALUE = "1"


def set_debug_mode(debug: bool) -> None:
    os.environ[ARG_NAME] = str(int(debug))


def is_debug() -> bool:
    return os.environ[ARG_NAME] == ARG_VALUE
