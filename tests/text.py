from __future__ import annotations

from typing import ClassVar

from .abc.base import TestBase


class TestTextClass(TestBase):

    ASSET_FILES: ClassVar[list[str]] = ["comment.html"]
    NUM_SOURCE_TEXT_NODES: ClassVar[int] = 2
    NUM_RECOVERED_TEXT_NODES: ClassVar[int] = 0

    def test_check_comments_captured_as_text_nodes(self) -> None:
        doc = self.DB.documents()[0]
        source_summary = doc.source_summary()
        assert source_summary.text_node_count() == self.NUM_SOURCE_TEXT_NODES
        recovered_summary = doc.recovered_summary()
        assert recovered_summary.text_node_count() == self.NUM_RECOVERED_TEXT_NODES
