from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from star_discovery.summaries import compare_summaries, RevealResult, SubtreeSummary
from star_discovery.recovery.nodes.html_element_root import HTMLElementRootNode

if TYPE_CHECKING:
    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.abc.base import BaseNode


class Document:
    """Represents a document being recovered. Its intended to be the flip
    side of a star_discovery.input.Document instance, which represents
    the (faux) encrypted HTML element."""

    desc: str

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

    def __init__(self, desc: str, root_node: HTMLElementRootNode):
        self.desc = desc
        self._root_node = root_node
        self._frontier_nodes = frozenset((self._root_node,))

    def __str__(self) -> str:
        return (
            f"Input document '{self.desc}': "
            f"recovered {self.recovered_summary().total()} "
            f"of {self.source_summary().total()} nodes."
        )

    def to_html(self, inc_hidden: bool = False) -> BeautifulSoup:
        doc = BeautifulSoup()
        self._root_node.add_to_html(doc, inc_hidden)
        return doc

    def reveal(self, keys: KeyCollection, logger: Logger) -> RevealResult:
        result = RevealResult()
        for node in self._frontier_nodes:
            node_result = node.reveal(keys)
            result.merge_in(node_result)
        self._frontier_nodes = frozenset(result.frontier)
        self._recovered_nodes |= result.recovered
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

    def recovered_summary(self, logger: Logger | None = None) -> SubtreeSummary:
        if not (count := self._root_node.recovered_summary(logger)):
            if logger:
                logger.debug("document contains no recovered nodes for SubtreeSummary")
            return SubtreeSummary()
        return count

    def source_summary(self) -> SubtreeSummary:
        return self._root_node.source_summary()

    def validate(self, logger: Logger | None = None) -> bool:
        """Perform a number of internal consistency checks that are too
        expensive to check in normal use."""

        # Check to make sure all nodes in the HTML document are correctly
        # accounted for.
        source_nodes = self.source_summary()
        revealed_nodes = self.recovered_summary()
        hidden_nodes = SubtreeSummary()
        for frontier_node in self._frontier_nodes:
            hidden_nodes += frontier_node.source_summary()
        input_nodes = revealed_nodes + hidden_nodes
        if source_nodes == input_nodes:
            return True

        if differences := compare_summaries(source_nodes, revealed_nodes, hidden_nodes):
            for category, a_diff in differences:
                msg = (
                    f"Missing node(s): category={category}, value='{(a_diff.key)[:25]}', "
                    f"source={a_diff.source} {a_diff.comparison} "
                    f"revealed={a_diff.revealed} + hidden={a_diff.hidden}"
                )
                if not logger:
                    raise ValueError(msg)
                logger.error(msg)
            raise ValueError("Recovery document validation failed.")
        return False


def create(desc: str, html_doc: BeautifulSoup) -> Document:
    return Document(desc, HTMLElementRootNode(html_doc))
