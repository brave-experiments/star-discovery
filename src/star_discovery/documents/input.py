from __future__ import annotations

from typing import TYPE_CHECKING

from star_discovery.documents.recovered import Node, HTMLElementRootNode
from star_discovery.logging import get_logger
from star_discovery.types import RevealResult

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    from bs4.element import Tag as BSTag

    from star_discovery.logging import Logger
    from star_discovery.types import KeyMaterial, RecoveredKey


type HTMLDoc = BeautifulSoup


class Document:
    desc: str
    _bs_doc: HTMLDoc
    _root_node: HTMLElementRootNode
    _collection: DocumentCollection

    _frontier_nodes: frozenset[Node] = frozenset()
    """Track all leaf nodes that haven't been recovered.  Note
    that this will grow (for a while) as more of the document is
    recovered, since initially the entire document is uncovered, and
    so the "frontier" is the root of the tree."""

    _recovered_nodes: set[Node] = set()
    """All nodes in the document that have been recovered so far.  Note that
    this is mostly redundant, since these are already walkable through
    the `_root_node` property."""

    _logger: Logger

    def __init__(self, collection: DocumentCollection, bs_doc: HTMLDoc, desc: str):
        self.desc = desc
        self._collection = collection
        self._logger = collection._logger
        self._bs_doc = bs_doc

        root_tag_name = self._bs_doc.ROOT_TAG_NAME
        root_tag = self._bs_doc.find(root_tag_name, recursive=False)
        assert root_tag is not None

        self._root_node = HTMLElementRootNode(root_tag)
        self._frontier_nodes = frozenset((self._root_node,))

    def __str__(self) -> str:
        num_nodes = self._root_node.source_count.count()
        return f"Document: '{self.desc}' ({num_nodes:d} nodes)"

    def reveal(self, keys: frozenset[RecoveredKey]) -> RevealResult:
        result = RevealResult()
        for node in self._frontier_nodes:
            node_result = node.reveal(keys)
            result.merge_in(node_result)
        self._frontier_nodes = frozenset(result.frontier)
        self._recovered_nodes |= result.recovered
        self._logger.debug(
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


class DocumentCollection:
    _threshold: int
    """The number of different documents that must have included a given
    key (or in our simulated key, path to an element) for the key to
    be recovered."""

    _documents: list[Document] = []
    """Simple list to keep track of all the documents in this collection."""

    _key_sources: dict[KeyMaterial, set[Document]] = {}
    """Keep track of how many documents include a node with the the given
    node path. The size of this allows us to keep track of whether
    we've hit the given K threshold, and keeping the documents as a list
    instead of a count allows us to keep track of which documents are
    responsible for which matches.

    Note that this has the additional benefit of making sure that the same
    document can't count towards the "unlock" threshold twice,
    which can happen in cases like the below when we're _not_ treating
    the node's position in its key. (We wouldn't want this to count as
    two instances of unlocking the "span" elements).
    <div>
     <span />
     <span />
    </div>"""

    _recovered_keys: set[RecoveredKey] = set()
    """The keys that have have at least `threshold` documents contributing
    key material."""

    _round: int = 0
    """Keep track of how many rounds of a. reveal (i.e., recover all nodes
    possible in included documents given the currently recovered keys)
    and b. collect (i.e., collect all key material possible from frontier
    nodes, to see if we're able to recover any additional keys)."""

    _logger: Logger = get_logger()

    def reveal_round(self) -> RevealResult:
        result = RevealResult()
        current_keys = frozenset(self._recovered_keys)
        for doc in self._documents:
            doc_result = doc.reveal(current_keys)
            self._update_key_material(doc, doc_result)
            result.merge_in(doc_result)
        return result

    def collect_round(self) -> int:
        return self._update_recovered_keys()

    def add_document(self, bs_doc: HTMLDoc, desc: str) -> None:
        prev_total_nodes = self.total_known_nodes()

        new_doc = Document(self, bs_doc, desc)
        self._logger.info("Adding document to collection: ", new_doc)
        self._documents.append(new_doc)

        current_total_known_nodes = self.total_known_nodes()
        while prev_total_nodes != current_total_known_nodes:
            prev_total_nodes = current_total_known_nodes
            self._round += 1
            self.reveal_round()
            self.collect_round()
            current_total_known_nodes = self.total_known_nodes()
            self._logger.debug(
                f"round {self._round} ({len(self._documents)} docs): "
                f" keys: {len(self._recovered_keys)}, "
                f" recovered nodes: {self.total_recovered_nodes()}, "
                f" frontier nodes: {self.total_frontier_nodes()}"
            )

    def total_frontier_nodes(self) -> int:
        return sum((x.num_frontier_nodes() for x in self._documents))

    def total_recovered_nodes(self) -> int:
        return sum((x.num_recovered_nodes() for x in self._documents))

    def total_known_nodes(self) -> int:
        return self.total_frontier_nodes() + self.total_recovered_nodes()

    def _update_key_material(self, doc: Document, result: RevealResult) -> None:
        """Update the `key_sources` property, which tracks which documents
        contain at least one recovered node for each path (or, each simulated
        key)."""
        # Note this is not the most efficient way of doing this, but its
        # the most concise to code. If we wanted to optimize the implementation
        # we could keep track of which key contributions are coming from
        # frontier nodes, and only check if those have passed the threshold.
        seen_nodes: set[Node] = result.recovered | result.frontier
        for node in seen_nodes:
            key_material = node.path
            self._key_sources.setdefault(key_material, set()).add(doc)

    def _update_recovered_keys(self) -> int:
        """Update the `recovered_keys` property, so that it contains all
        the keys that have at least "`threshold`" documents contributing
        key material to it.

        Return the number of new keys that have been recovered, since
        the last time this was called."""
        # This is also not optimized. If we wanted to we could keep track
        # of which keys are at their threshold and which aren't, and save
        # some work. But, this implementation is simpler and more straight
        # forward, and (I expect) easier to follow, and so "optimizing"
        # for that.
        prev_key_count = len(self._recovered_keys)
        for key, docs in self._key_sources.items():
            if len(docs) >= self._threshold:
                self._recovered_keys.add(key)
        return len(self._recovered_keys) - prev_key_count
