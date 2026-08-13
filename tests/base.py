from __future__ import annotations

from abc import ABC
from typing import ClassVar, TYPE_CHECKING

from bs4 import BeautifulSoup

from star_discovery.logging import config, Logger
from star_discovery.inputs.db import Database

if TYPE_CHECKING:
    from pathlib import Path


# pylint: disable-next=too-few-public-methods
class TestBase(ABC):
    INPUT_FILES: ClassVar[list[Path]]
    THRESHOLD: ClassVar[int] = 2
    LOGGER: ClassVar[Logger] = config("quiet")

    DB: ClassVar[Database]

    @classmethod
    def setup_class(cls) -> None:
        db = Database(cls.THRESHOLD)
        for input_path in cls.INPUT_FILES:
            html_data = BeautifulSoup(input_path.read_text(), features="html.parser")
            db.add_document(html_data, input_path, cls.LOGGER)
        cls.DB = db
