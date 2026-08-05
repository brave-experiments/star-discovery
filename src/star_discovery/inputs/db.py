import pickle
from typing import Any, ClassVar, TYPE_CHECKING

from packaging.version import Version

import star_discovery
from star_discovery.inputs.document import Document
from star_discovery.types import RevealResult

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup

    from star_discovery.recovery.abc.base import BaseNode
    from star_discovery.logging import Logger
    from star_discovery.types import KeyMaterial, RecoveredKey


class Database:
    DEFAULT_FILENAME: ClassVar[str] = "star-discovery.db"

    logger: Logger | None

    version: Version = Version(star_discovery.__version__)
    """The version of this library that a database instance was created
    with (used when loading pickled instances from disk.)"""

    threshold: int
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

    def __init__(self, threshold: int, logger: Logger | None = None):
        self.threshold = threshold
        self.logger = logger

    def __str__(self) -> str:
        return (
            f"STAR-Discovery Database: (# documents: {len(self._documents)}, "
            f"# threshold: {self.threshold}, version: {self.version}, "
            f"# recovered keys: {len(self._recovered_keys)}, "
            f"# recovered nodes: {self.total_recovered_nodes()})"
        )

    def __getstate__(self) -> Any:
        """Implement the pickle 'dunder' methods so make sure none of the logger
        state or configuration is saved in the pickle'd data, since 1. we want
        that configuration to change per invocation / re-hydration, and
        2. saving the logger object could also persist streams to files on
        disk (and other external state like that) which we don't want to
        mix up."""
        state = self.__dict__.copy()
        del state["logger"]
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        self.__dict__.update(state)
        self.logger = None

    def reveal_round(self) -> RevealResult:
        result = RevealResult()
        current_keys = frozenset(self._recovered_keys)
        for index, doc in enumerate(self._documents):
            doc_result = doc.reveal(current_keys, self.logger)
            if self.logger:
                self.logger.debug(
                    f"    Round {self._round} (Doc {index + 1} / {self.num_docs()}): "
                    + str(doc_result),
                )
            self._update_key_material(doc, doc_result)
            result.merge_in(doc_result)
        return result

    def collect_round(self) -> int:
        return self._update_recovered_keys()

    def add_document(self, bs_doc: BeautifulSoup, desc: str) -> None:
        prev_known_nodes = self.total_known_nodes()

        new_doc = Document(bs_doc, desc)
        if self.logger:
            self.logger.info(f"Adding document to collection: {new_doc}")
        self._documents.append(new_doc)

        curr_known_nodes = self.total_known_nodes()
        if self.logger:
            self.logger.debug(f" - Previously knew of {prev_known_nodes} nodes")
            self.logger.debug(f" - Now know of {curr_known_nodes} nodes")

        any_new_keys = False
        any_new_nodes = prev_known_nodes < curr_known_nodes

        while any_new_keys or any_new_nodes:
            prev_recovered_nodes = self.total_recovered_nodes()
            prev_frontier_nodes = self.total_frontier_nodes()
            prev_recovered_keys = self.total_recovered_keys()

            self._round += 1
            if self.logger:
                self.logger.debug(
                    f"Start Round {self._round} w/ {len(self._recovered_keys)} keys"
                    + "=====",
                )
            self.reveal_round()
            self.collect_round()

            curr_recovered_nodes = self.total_recovered_nodes()
            curr_frontier_nodes = self.total_frontier_nodes()
            curr_known_nodes = self.total_known_nodes()
            curr_recovered_keys = self.total_recovered_keys()

            any_new_keys = curr_recovered_keys > prev_recovered_keys
            prev_total_nodes = prev_recovered_nodes + prev_frontier_nodes
            any_new_nodes = curr_known_nodes > prev_total_nodes
            if self.logger:
                self.logger.debug(
                    f"\tEnd Round {self._round}. (prev -> curr)\n"
                    f"\t\tRecovered nodes:\t{prev_recovered_nodes} -> {curr_recovered_nodes}\n"
                    f"\t\tFrontier nodes:\t{prev_frontier_nodes} -> {curr_frontier_nodes}\n"
                    f"\t\tRecovered keys:\t{prev_recovered_keys} -> {curr_recovered_keys}\n"
                )

    def documents(self) -> list[Document]:
        return self._documents

    def num_docs(self) -> int:
        return len(self._documents)

    def total_frontier_nodes(self) -> int:
        return sum((x.num_frontier_nodes() for x in self._documents))

    def total_recovered_nodes(self) -> int:
        return sum((x.num_recovered_nodes() for x in self._documents))

    def total_known_nodes(self) -> int:
        return self.total_frontier_nodes() + self.total_recovered_nodes()

    def total_recovered_keys(self) -> int:
        return len(self._recovered_keys)

    def _update_key_material(self, doc: Document, result: RevealResult) -> None:
        """Update the `key_sources` property, which tracks which documents
        contain at least one recovered node for each path (or, each simulated
        key)."""
        # Note this is not the most efficient way of doing this, but its
        # the most concise to code. If we wanted to optimize the implementation
        # we could keep track of which key contributions are coming from
        # frontier nodes, and only check if those have passed the threshold.
        seen_nodes: set[BaseNode] = result.recovered | result.frontier
        for node in seen_nodes:
            key_material = node.path
            try:
                self._key_sources[key_material].add(doc)
            except KeyError:
                self._key_sources[key_material] = set((doc,))

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
            if len(docs) >= self.threshold:
                self._recovered_keys.add(key)
        return len(self._recovered_keys) - prev_key_count


def create(path: Path, threshold: int) -> Database:
    try:
        db = Database(threshold)
        data = pickle.dumps(db)
        path.write_bytes(data)
        return db
    except (pickle.PickleError, OSError) as exc:
        msg = f"Unable to create Database instance to path '{path}'"
        raise ValueError(msg) from exc


def load(path: Path) -> Database:
    try:
        data = path.read_bytes()
        db = pickle.loads(data)
        assert isinstance(db, Database)
        return db
    except (pickle.PickleError, OSError) as exc:
        msg = f"Unable to load Database instance from path '{path}'"
        raise ValueError(msg) from exc
