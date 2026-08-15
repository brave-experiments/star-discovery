from __future__ import annotations

from pathlib import Path
from typing import ClassVar, TYPE_CHECKING

from .abc.base import TestBase
from ..paths import ASSET_HTML_DIR

if TYPE_CHECKING:
    from star_discovery.inputs.db import Database


class TestTextClass(TestBase):

    INPUT_FILES: ClassVar[list[Path]] = [ASSET_HTML_DIR / "comment.html"]
    NUM_SOURCE_TEXT_NODES: ClassVar[int] = 2
    NUM_RECOVERED_TEXT_NODES: ClassVar[int] = 0

    def test_check_comments_captured_as_text_nodes(self) -> None:
        doc = self.DB.documents()[0]
        source_summary = doc.source_summary()
        assert source_summary.text_node_count() == self.NUM_SOURCE_TEXT_NODES
        recovered_summary = doc.recovered_summary()
        assert recovered_summary.text_node_count() == self.NUM_RECOVERED_TEXT_NODES
