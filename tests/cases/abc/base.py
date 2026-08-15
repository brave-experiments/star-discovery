from __future__ import annotations

from abc import ABC
from tempfile import gettempdir
from typing import ClassVar
from pathlib import Path

from bs4 import BeautifulSoup

from star_discovery.logging import config, Logger
from star_discovery.inputs.db import Database


class TestBase(ABC):
    INPUT_FILES: ClassVar[list[Path]] = []
    TEMP_FILES: ClassVar[list[Path]] = []

    THRESHOLD: ClassVar[int] = 2
    LOGGER: ClassVar[Logger] = config("quiet")
    TEMP_ROOT: ClassVar[Path] = Path(gettempdir())

    DB: ClassVar[Database]

    @classmethod
    def setup_class(cls) -> None:
        db = Database(cls.THRESHOLD)
        for input_path in cls.INPUT_FILES:
            html_data = BeautifulSoup(input_path.read_text(), features="html.parser")
            db.add_document(html_data, input_path, cls.LOGGER)
        cls.DB = db

    @classmethod
    def teardown_class(cls) -> None:
        for temp_path in cls.TEMP_FILES:
            if temp_path.exists():
                temp_path.unlink()
