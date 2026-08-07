from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from star_discovery.summaries import NodeCount, RevealResult
from star_discovery.recovery.document import create, Document as RecoveryDocument

if TYPE_CHECKING:
    from pathlib import Path

    from star_discovery.logging import Logger
    from star_discovery.recovery.type_aliases import RecoveredKey


@dataclass
class RecoverySummary:
    recovered: NodeCount
    source: NodeCount

    def html_node_recovery_pct(self) -> float:
        return self.recovered.html_node_count() / float(self.source.html_node_count())

    def text_node_recovery_pct(self) -> float:
        return self.recovered.text_node_count() / float(self.source.text_node_count())

    def attr_name_recovery_pct(self) -> float:
        return self.recovered.attr_name_count() / float(self.source.attr_name_count())

    def attr_value_recovery_pct(self) -> float:
        return self.recovered.attr_value_count() / float(self.source.attr_value_count())

    def html_class_recovery_pct(self) -> float:
        return self.recovered.html_class_count() / float(self.source.html_class_count())


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
            f"{self.recovered_count().total()} of "
            f"{self.source_count().total()} nodes recovered "
            f"({self.pct_recovered()}%)"
        )

    def summary(self, logger: Logger | None = None) -> RecoverySummary:
        return RecoverySummary(self.recovered_count(logger), self.source_count())

    def reveal(self, keys: frozenset[RecoveredKey], logger: Logger) -> RevealResult:
        return self._recovery_doc.reveal(keys, logger)

    def recovered_html(self, inc_hidden: bool = False) -> BeautifulSoup:
        return self._recovery_doc.to_html(inc_hidden)

    def num_frontier_nodes(self) -> int:
        return self._recovery_doc.num_frontier_nodes()

    def num_recovered_nodes(self) -> int:
        return self._recovery_doc.num_recovered_nodes()

    def num_known_nodes(self) -> int:
        return self._recovery_doc.num_known_nodes()

    def recovered_count(self, logger: Logger | None = None) -> NodeCount:
        return self._recovery_doc.recovered_count(logger)

    def source_count(self) -> NodeCount:
        return self._recovery_doc.source_count()

    def pct_recovered(self) -> float:
        total_pct = self.recovered_count().total() / self.source_count().total()
        return round(total_pct, 2)
