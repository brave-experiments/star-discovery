from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import nan
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from star_discovery.summaries import DepthSummary, SubtreeSummary, RevealResult
from star_discovery.recovery.document import create, Document as RecoveryDocument

if TYPE_CHECKING:
    from pathlib import Path

    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger


@dataclass
class RecoverySummary:
    recovered: SubtreeSummary
    source: SubtreeSummary

    def html_node_recovery_pct(self) -> float:
        try:
            return self.recovered.html_node_count() / float(
                self.source.html_node_count()
            )
        except ZeroDivisionError:
            return nan

    def text_node_recovery_pct(self) -> float:
        try:
            return self.recovered.text_node_count() / float(
                self.source.text_node_count()
            )
        except ZeroDivisionError:
            return nan

    def attr_name_recovery_pct(self) -> float:
        try:
            return self.recovered.attr_name_count() / float(
                self.source.attr_name_count()
            )
        except ZeroDivisionError:
            return nan

    def attr_value_recovery_pct(self) -> float:
        try:
            return self.recovered.attr_value_count() / float(
                self.source.attr_value_count()
            )
        except ZeroDivisionError:
            return nan


class Document:
    path: Path
    timestamp: datetime
    _recovery_doc: RecoveryDocument

    def __init__(self, input_doc: BeautifulSoup, path: Path):
        self.path = path
        self.timestamp = datetime.now()
        self._recovery_doc = create(str(path), input_doc)

    def __str__(self) -> str:
        return f"Input Document: {self.path} @ {self.timestamp}"

    def recovery_desc(self) -> str:
        return (
            f"{self.recovered_summary().total()} of "
            f"{self.source_summary().total()} nodes recovered "
            f"({self.pct_recovered()}%)"
        )

    def summary(self, logger: Logger | None = None) -> RecoverySummary:
        return RecoverySummary(self.recovered_summary(logger), self.source_summary())

    def source_depth(self) -> int:
        """Returns the maximum length from the root node in the HTML document
        to a leaf node."""
        return self._recovery_doc.source_depth()

    def recovered_depths_summary(self) -> DepthSummary:
        return self._recovery_doc.recovered_depths_summary()

    def recovered_depth(self) -> int:
        return self._recovery_doc.recovered_depth()

    def source_depths_summary(self) -> DepthSummary:
        return self._recovery_doc.source_depths_summary()

    def reveal(self, keys: KeyCollection, logger: Logger) -> RevealResult:
        return self._recovery_doc.reveal(keys, logger)

    def recovered_html(self, inc_hidden: bool = False) -> BeautifulSoup:
        return self._recovery_doc.to_html(inc_hidden)

    def num_frontier_nodes(self) -> int:
        return self._recovery_doc.num_frontier_nodes()

    def num_recovered_nodes(self) -> int:
        return self._recovery_doc.num_recovered_nodes()

    def num_known_nodes(self) -> int:
        return self._recovery_doc.num_known_nodes()

    def recovered_summary(self, logger: Logger | None = None) -> SubtreeSummary:
        return self._recovery_doc.recovered_summary(logger)

    def source_summary(self) -> SubtreeSummary:
        return self._recovery_doc.source_summary()

    def pct_recovered(self) -> float:
        total_pct = self.recovered_summary().total() / self.source_summary().total()
        return round(total_pct, 2)

    def validate(self, logger: Logger | None) -> bool:
        return self._recovery_doc.validate(logger)
