from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from star_discovery.recovery.abc.base import BaseNode
from star_discovery.recovery.html_element_root import HTMLElementRootNode
from star_discovery.types import RevealResult

if TYPE_CHECKING:
    from star_discovery.logging import Logger
    from star_discovery.types import KeyMaterial, RecoveredKey


class Document:
    desc: str
    _bs_doc: BeautifulSoup
    _root_node: HTMLElementRootNode

    _frontier_nodes: frozenset[BaseNode] = frozenset()
    """Track all leaf nodes that haven't been recovered.  Note
    that this will grow (for a while) as more of the document is
    recovered, since initially the entire document is uncovered, and
    so the "frontier" is the root of the tree."""

    _recovered_nodes: set[BaseNode] = set()
    """All nodes in the document that have been recovered so far.  Note that
    this is mostly redundant, since these are already walkable through
    the `_root_node` property."""

    def __init__(self, bs_doc: BeautifulSoup, desc: str):
        self.desc = desc
        self._bs_doc = bs_doc

        root_tag = self._bs_doc.find("html", recursive=False)
        assert root_tag is not None

        self._root_node = HTMLElementRootNode(root_tag)
        self._frontier_nodes = frozenset((self._root_node,))

    def __str__(self) -> str:
        num_nodes = self._root_node.source_count.count()
        return f"Document: '{self.desc}' ({num_nodes:d} nodes)"

    def to_html(self) -> BeautifulSoup:
        doc = BeautifulSoup()
        self._root_node.add_to_html(doc)
        return doc

    def reveal(
        self, keys: frozenset[RecoveredKey], logger: Logger | None = None
    ) -> RevealResult:
        result = RevealResult()
        for node in self._frontier_nodes:
            node_result = node.reveal(keys)
            result.merge_in(node_result)
        self._frontier_nodes = frozenset(result.frontier)
        self._recovered_nodes |= result.recovered
        if logger:
            logger.debug(
                f"reveal result for {self.desc} -> "
                f"total recovered nodes: {self.num_recovered_nodes()}, "
                f"newly recovered nodes: {len(result.recovered)}, "
                f"newly frontier nodes: {len(result.frontier)}"
            )
        return result

    def num_frontier_nodes(self) -> int:
        return len(self._frontier_nodes)

    def num_recovered_nodes(self) -> int:
        return len(self._recovered_nodes)

    def num_known_nodes(self) -> int:
        return self.num_frontier_nodes() + self.num_recovered_nodes()
