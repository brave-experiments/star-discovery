from __future__ import annotations

from hashlib import sha256
from typing import ClassVar, override, TYPE_CHECKING

from bs4.element import Comment, NavigableString

from star_discovery.summaries import NodeCount
from star_discovery.recovery.nodes.abc.html_base import HTMLBaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
    from star_discovery.recovery.type_aliases import BSItem


class HTMLTextNode(HTMLBaseNode):
    SEGMENT_PREFIX: ClassVar[str] = "text"

    _elm: NavigableString

    @override
    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, NavigableString)
        count: NodeCount = NodeCount()
        count.add_text_node(item)
        return count

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
        self._elm = NavigableString(trimmed_text)
        super().__init__(parent, index)

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
    def as_html_text_node(self) -> HTMLTextNode | None:
        return self

    @override
    def count_for_recovered_doc(self, logger: Logger | None) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding text to NodeCount: {self.trim()}")
        count.add_text_node(self._elm)
        return count

    def trim(self, max_length: int = 10) -> str:
        if len(self._elm) <= max_length:
            return self._elm
        return f"{self._elm[:10]}…"
