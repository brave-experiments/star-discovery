from __future__ import annotations

from typing import ClassVar, TYPE_CHECKING

from bs4.element import NavigableString, Tag

from .abc.base import TestBase

if TYPE_CHECKING:
    from bs4 import BeautifulSoup


def get_element_counts(html: BeautifulSoup) -> tuple[int, int]:
    """Return the number of html nodes, and non-whitespace text
    nodes (respectively) in the HTML text."""
    num_html_nodes = 0
    num_text_nodes = 0

    root_html_node = html.find("html")
    assert root_html_node
    num_html_nodes += 1  # to include the <html> element itself.
    for child_elm in root_html_node.descendants:
        if isinstance(child_elm, Tag):
            num_html_nodes += 1
            continue

        if isinstance(child_elm, NavigableString):
            # We only track non-whitespace nodes in star-discovery,
            # so skip over any whitespace nodes in the BeautifulSoup
            # version of the document too.
            if len(child_elm.strip()) > 0:
                num_text_nodes += 1
    return num_html_nodes, num_text_nodes


class TestSourceClass(TestBase):

    ASSET_FILES: ClassVar[list[str]] = [
        "basic-1.html",
        "cnn_com-US.html",
    ]

    BASIC_HTML_INDEX: ClassVar[int] = 0
    COMPLEX_HTML_INDEX: ClassVar[int] = 1

    def test_simple_source_summary_matches_bs_definition(self) -> None:
        doc = self.DB.documents()[self.BASIC_HTML_INDEX]
        html = self.HTML_DATA[self.BASIC_HTML_INDEX]

        num_html_nodes, num_text_nodes = get_element_counts(html)

        doc_summary = doc.summary()
        doc_source_summary = doc_summary.source
        assert doc_source_summary.html_node_count() == num_html_nodes
        assert doc_source_summary.text_node_count() == num_text_nodes

    def test_complex_source_summary_matches_bs_definition(self) -> None:
        doc = self.DB.documents()[self.COMPLEX_HTML_INDEX]
        html = self.HTML_DATA[self.COMPLEX_HTML_INDEX]

        num_html_nodes, num_text_nodes = get_element_counts(html)

        doc_summary = doc.summary()
        doc_source_summary = doc_summary.source
        assert doc_source_summary.html_node_count() == num_html_nodes
        assert doc_source_summary.text_node_count() == num_text_nodes
