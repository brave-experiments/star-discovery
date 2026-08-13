from __future__ import annotations

from hashlib import sha256
from typing import ClassVar, override, TYPE_CHECKING

from bs4.element import Comment, NavigableString

from star_discovery.summaries import SubtreeSummary
from star_discovery.recovery.nodes.abc.html_base import HTMLBaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode


class HTMLTextNode(HTMLBaseNode):
    SEGMENT_PREFIX: ClassVar[str] = "text"

    _elm: NavigableString

    @classmethod
    def is_relevant_text(cls, text: NavigableString) -> NavigableString | None:
        trimmed_text = text.strip()
        if len(trimmed_text) > 0:
            return NavigableString(trimmed_text)
        return None

    def __init__(self, parent: HTMLElementBaseNode, elm: NavigableString, index: int):
        trimmed_text = elm.output_ready().strip()
        text_bytes = trimmed_text.encode("utf8")
        self._value = sha256(text_bytes, usedforsecurity=False).hexdigest()
        super().__init__(parent, NavigableString(trimmed_text), index)

    def __str__(self) -> str:
        return f"[text: '{self.trim()}']"

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            item.append(Comment(self._elm))
            return True
        if self._is_recovered:
            item.append(NavigableString(self._elm))
            return True
        return False

    @override
    def summary_for_recovered_doc(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (count := super().summary_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding text to SubtreeSummary: {self.trim()}")
        count.add_text_node(self._elm)
        return count

    @override
    def source_summary(self) -> SubtreeSummary:
        return SubtreeSummary.with_text_node(self._elm)

    def trim(self, max_length: int = 10) -> str:
        if len(self._elm) <= max_length:
            return self._elm
        return f"{self._elm[:10]}…"
