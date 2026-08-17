from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import ClassVar

from bs4 import BeautifulSoup

from star_discovery.debug import set_debug_mode
from star_discovery.logging import config, Logger
from star_discovery.inputs.db import Database

TEST_DIR = Path(__file__).parent.parent.absolute()
ASSETS_PATH_DIR = TEST_DIR / "assets"


# pylint: disable-next=too-few-public-methods
class TestBase(ABC):
    ASSET_FILES: ClassVar[list[str]] = []

    THRESHOLD: ClassVar[int] = 2
    LOGGER: ClassVar[Logger] = config("quiet")

    HTML_DATA: ClassVar[list[BeautifulSoup]]
    """The BeautifulSoup representation of each HTML file specified in the
    test class's ASSET_FILES property."""

    DB: ClassVar[Database]
    """A star_discovery.input.DB instance, with each HTML document defined in
    the test class's ASSET_FILES property loaded."""

    @classmethod
    def setup_class(cls) -> None:
        # We want tests to run fast, not produce debugging output.
        set_debug_mode(False)
        db = Database(cls.THRESHOLD)
        cls.HTML_DATA = []
        for input_file in cls.ASSET_FILES:
            asset_path = ASSETS_PATH_DIR / input_file
            html_data = BeautifulSoup(asset_path.read_text(), features="html.parser")
            cls.HTML_DATA.append(html_data)
            db.add_document(html_data, asset_path, cls.LOGGER)
        cls.DB = db
