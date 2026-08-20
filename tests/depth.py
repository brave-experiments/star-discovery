from __future__ import annotations

from typing import ClassVar

from star_discovery.summaries import NodeType

from .abc.base import TestBase

DOC_SOURCE_DEPTH = 10
DEEPEST_RECOVERED_NODE_DEPTH = 10
DEEPEST_UNRECOVERED_NODE_DEPTH = 9


class TestDepthClass(TestBase):

    ASSET_FILES: ClassVar[list[str]] = [
        "depth-1.html",
        "depth-2.html",
    ]

    def test_source_depth(self) -> None:
        doc = self.DB.documents()[0]
        assert doc.source_depth() == DOC_SOURCE_DEPTH

    def test_recovered_depth(self) -> None:
        doc = self.DB.documents()[0]
        assert doc.recovered_depth() == DOC_SOURCE_DEPTH

    def test_recovered_depth_summary(self) -> None:
        doc = self.DB.documents()[0]
        recovered_depths_summary = doc.recovered_depths_summary()
        depth_ten_summary = recovered_depths_summary[DEEPEST_RECOVERED_NODE_DEPTH]
        assert depth_ten_summary[NodeType.TEXT] == 1
