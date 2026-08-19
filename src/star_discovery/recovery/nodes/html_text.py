from __future__ import annotations

from hashlib import sha256
from typing import override, TYPE_CHECKING

from bs4.element import Comment, NavigableString

from star_discovery.summaries import NodeDepth, NodeType, SubtreeSummary
from star_discovery.recovery.nodes.abc.html_base import HTMLBaseNode

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import ClassVar

    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode


def trim_navigable_string(elm: NavigableString) -> NavigableString | None:
    trimmed_text = elm.strip()
    if len(trimmed_text) > 0:
        return NavigableString(trimmed_text)
    return None


class HTMLTextNode(HTMLBaseNode):
    SEGMENT_PREFIX: ClassVar[str] = "text"

    _elm: NavigableString

    @classmethod
    def relevant_text(cls, elm: NavigableString) -> NavigableString | None:
        return trim_navigable_string(elm)

    def __init__(
        self, depth: int, parent: HTMLElementBaseNode, elm: NavigableString, index: int
    ):
        trimmed_text = trim_navigable_string(elm)
        assert trimmed_text
        text_bytes = trimmed_text.encode("utf8")
        self._value = sha256(text_bytes, usedforsecurity=False).hexdigest()
        super().__init__(depth, parent, trimmed_text, index)

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
        if relevant_text := HTMLTextNode.relevant_text(self._elm):
            count.add_text_node(relevant_text)
        return count

    @override
    def source_summary(self) -> SubtreeSummary:
        summary = SubtreeSummary()
        if relevant_text := HTMLTextNode.relevant_text(self._elm):
            summary.add_text_node(relevant_text)
        return summary

    @override
    def max_depth(self) -> int:
        return self.depth()

    def node_depths(self) -> Generator[NodeDepth]:
        if not self.is_recovered():
            return
        yield NodeDepth(self.depth(), NodeType.TEXT)

    def trim(self, max_length: int = 10) -> str:
        if len(self._elm) <= max_length:
            return self._elm
        return f"{self._elm[:10]}…"
