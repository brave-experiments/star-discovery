from __future__ import annotations

from dataclasses import dataclass
import pickle
from typing import ClassVar, TYPE_CHECKING

from packaging.version import Version

import star_discovery
from star_discovery.key_store import KeyStore
from star_discovery.inputs.document import Document
from star_discovery.summaries import RevealResult

if TYPE_CHECKING:
    from pathlib import Path

    from bs4 import BeautifulSoup

    from star_discovery.logging import Logger


type DocRevealResult = tuple[Document, RevealResult]


@dataclass
class RecoveryState:
    recovered: int
    frontier: int
    total: int
    keys: int


class Database:
    DEFAULT_FILENAME: ClassVar[str] = "star-discovery.db"

    version: Version = Version(star_discovery.__version__)
    """The version of this library that a database instance was created
    with (used when loading pickled instances from disk.)"""

    threshold: int
    """The number of different documents that must have included a given
    key (or in our simulated key, path to an element) for the key to
    be recovered."""

    _documents: list[Document]
    """Simple list to keep track of all the documents in this collection."""

    _key_store: KeyStore
    """Data structure to keep track of how many shares for each key
    have been discovered, and which keys have enough shares to be
    'recovered'."""

    _round: int
    """Keep track of how many rounds of a. reveal (i.e., recover all nodes
    possible in included documents given the currently recovered keys)
    and b. collect (i.e., collect all key material possible from frontier
    nodes, to see if we're able to recover any additional keys)."""

    def __init__(self, threshold: int):
        self.threshold = threshold
        self._documents = []
        self._key_store = KeyStore(self.threshold)
        self._round = 0

    def __str__(self) -> str:
        return (
            f"STAR-Discovery Database: (# documents: {len(self._documents)}, "
            f"# threshold: {self.threshold}, version: {self.version}, "
            f"# recovered keys: {len(self._key_store.recovered_keys())}, "
            f"# recovered nodes: {self.total_recovered_nodes()})"
        )

    def save(self, path: Path, logger: Logger) -> None:
        data = pickle.dumps(self)
        path.write_bytes(data)
        logger.info(f"Successfully wrote database to {path}")

    def reveal_round(self, logger: Logger) -> list[DocRevealResult]:
        result = RevealResult()
        current_keys = self._key_store.recovered_keys()
        results_per_doc: list[DocRevealResult] = []
        for index, doc in enumerate(self._documents):
            doc_result = doc.reveal(current_keys, logger)
            logger.debug(
                f"    Round {self._round} "
                f"(Doc {index + 1} / {self.num_docs()}): {doc_result}",
            )
            results_per_doc.append((doc, doc_result))
            result.merge_in(doc_result)
            if __debug__:
                doc.validate()
        return results_per_doc

    def collect_round(self, reveal_results: list[DocRevealResult]) -> None:
        # Note this is not the most efficient way of doing this, but its
        # the most concise to code. If we wanted to optimize the implementation
        # we could keep track of which key contributions are coming from
        # frontier nodes, and only check if those have passed the threshold.
        for doc, reveal_result in reveal_results:
            seen_nodes = reveal_result.recovered | reveal_result.frontier
            for node in seen_nodes:
                self._key_store.add_key_share(doc, node.node_tag)

    def recovery_state(self) -> RecoveryState:
        return RecoveryState(
            self.total_recovered_nodes(),
            self.total_frontier_nodes(),
            self.total_known_nodes(),
            self.total_recovered_keys(),
        )

    def add_document(self, bs_doc: BeautifulSoup, path: Path, logger: Logger) -> None:
        prev_state = self.recovery_state()
        prev_known_nodes = self.total_known_nodes()

        new_doc = Document(bs_doc, path)
        logger.debug(f"Adding document to collection: {new_doc}")
        self._documents.append(new_doc)

        curr_state = self.recovery_state()
        logger.debug(f" - Previously knew of {prev_state.total} nodes")
        logger.debug(f" - Now know of {curr_state.total} nodes")

        any_new_keys = False
        any_new_nodes = prev_state.total < curr_state.total
        while any_new_keys or any_new_nodes:
            prev_state = curr_state
            self._round += 1
            logger.debug(
                f"Round {self._round} start: "
                f"{len(self._key_store.recovered_keys())} keys",
            )

            reveal_result = self.reveal_round(logger)
            self.collect_round(reveal_result)

            curr_state = self.recovery_state()
            any_new_keys = curr_state.keys > prev_state.keys
            any_new_nodes = curr_state.total > prev_state.total
            logger.debug(
                f"Round {self._round} end: "
                f"Recovered nodes: {prev_state.recovered} -> {curr_state.recovered}, "
                f"Frontier nodes: {prev_state.frontier} -> {curr_state.frontier}, "
                f"Recovered keys:{prev_state.keys} -> {curr_state.keys}"
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
        return len(self._key_store.recovered_keys())


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
