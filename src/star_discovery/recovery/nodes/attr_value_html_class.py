from __future__ import annotations

from typing import cast, TYPE_CHECKING

from bs4.element import AttributeValueList

from star_discovery.bs_helpers import unrecovered_attr_value
from star_discovery.recovery.nodes.abc.base import BaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.attr_key_html_class import AttrKeyHTMLClassNode
    from star_discovery.summaries import NodeCount


HTML_CLASS_ATTR_NAME = "class"


class AttrValueHTMLClassNode(BaseNode):
    SEGMENT_PREFIX = "html-class"

    def __init__(self, parent: AttrKeyHTMLClassNode, html_class: str):
        self._value = html_class
        super().__init__(parent)

    def __str__(self) -> str:
        return f"[class: {self._value}]"

    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            class_name = unrecovered_attr_value(self._value)
        elif self._is_recovered:
            class_name = self._value
        else:
            return False
        cast(AttributeValueList, item[HTML_CLASS_ATTR_NAME]).append(class_name)
        return True

    def as_attr_value_html_class_node(self) -> AttrValueHTMLClassNode | None:
        return self

    def count_for_recovered_doc(self, logger: Logger | None) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding html class to NodeCount: {self._value}")
        count.add_html_class(self._value)
        return count
