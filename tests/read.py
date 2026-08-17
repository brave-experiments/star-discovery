# pylint: disable=magic-value-comparison

from __future__ import annotations

from typing import ClassVar

from .abc.base import TestBase


class TestReadClass(TestBase):

    ASSET_FILES: ClassVar[list[str]] = [
        "basic-1.html",
        "basic-2.html",
    ]

    def test_doc_one_source_nodes(self) -> None:
        doc_one = self.DB.documents()[0]
        summary = doc_one.source_summary()
        assert summary.html_node_count() == 6
        assert summary.text_node_count() == 2
        assert summary.attr_name_count() == 3
        assert summary.attr_value_count() == 5

    def test_doc_one_recovered_nodes(self) -> None:
        doc_one = self.DB.documents()[0]
        summary = doc_one.summary().recovered
        assert summary.html_node_count() == 6
        assert summary.text_node_count() == 2
        assert summary.attr_name_count() == 3
        assert summary.attr_value_count() == 3

    def test_doc_two_source_nodes(self) -> None:
        doc_two = self.DB.documents()[1]
        summary = doc_two.source_summary()
        assert summary.html_node_count() == 8
        assert summary.text_node_count() == 4
        assert summary.attr_name_count() == 4
        assert summary.attr_value_count() == 6

    def test_doc_recovered_nodes_match(self) -> None:
        doc_one = self.DB.documents()[0]
        summary_one = doc_one.summary().recovered

        doc_two = self.DB.documents()[1]
        summary_two = doc_two.summary().recovered
        assert summary_one.html_node_count() == summary_two.html_node_count()
        assert summary_one.text_node_count() == summary_two.text_node_count()
        assert summary_one.attr_name_count() == summary_two.attr_name_count()
        assert summary_one.attr_value_count() == summary_two.attr_value_count()
