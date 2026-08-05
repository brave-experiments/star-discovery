from __future__ import annotations

from typing import cast, TYPE_CHECKING

from bs4.element import AttributeValueList

from star_discovery.recovery.abc.base import BaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.recovery.attr_key_html_class import AttrKeyHTMLClassNode
    from star_discovery.types import NodeCount


HTML_CLASS_ATTR_NAME = "class"


class AttrValueHTMLClassNode(BaseNode):
    SEGMENT_PREFIX = "html-class"

    def __init__(self, parent: AttrKeyHTMLClassNode, html_class: str):
        self._value = html_class
        super().__init__(parent)

    def __str__(self) -> str:
        return f"[class: {self._value}]"

    def add_to_html(self, item: Tag) -> bool:
        if not self._is_recovered:
            return False
        cast(AttributeValueList, item[HTML_CLASS_ATTR_NAME]).append(self._value)
        return True

    def as_attr_value_html_class_node(self) -> AttrValueHTMLClassNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_attr_value(self._value)
        return count
