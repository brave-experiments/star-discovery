from __future__ import annotations

from hashlib import sha256
from typing import TYPE_CHECKING

from bs4.element import NavigableString

from star_discovery.types import NodeCount
from star_discovery.recovery.abc.html_base import HTMLBaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.recovery.types import BSItem, HTMLParentNode


class HTMLTextNode(HTMLBaseNode):
    SEGMENT_PREFIX = "text"

    _elm: NavigableString

    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, NavigableString)
        count: NodeCount = NodeCount()
        count.add_text_node(item)
        return count

    def __init__(self, parent: HTMLParentNode, elm: NavigableString, index: int):
        text_bytes = elm.output_ready().encode("utf8")
        self._value = sha256(text_bytes, usedforsecurity=False).hexdigest()
        self._elm = elm
        super().__init__(parent, index)

    def __str__(self) -> str:
        return f"[text: '{self.text()}']"

    def add_to_html(self, item: Tag) -> bool:
        if not self._is_recovered:
            return False
        item.append(NavigableString(self._elm))
        return True

    def text(self, max_chars: int = 10) -> str:
        text = self._elm.output_ready()
        if len(text) <= max_chars:
            return text
        return text[0:max_chars] + "…"

    def as_html_text_node(self) -> HTMLTextNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_text_node(self._elm)
        return count
