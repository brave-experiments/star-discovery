from __future__ import annotations

from typing import cast, ClassVar, override, TYPE_CHECKING

from bs4.element import AttributeValueList

from star_discovery.bs_helpers import unrecovered_attr_value
from star_discovery.recovery.nodes.abc.base import BaseNode
from star_discovery.summaries import SubtreeSummary

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.attr_key_html_class import AttrKeyHTMLClassNode


HTML_CLASS_ATTR_NAME = "class"


class AttrValueHTMLClassNode(BaseNode):
    SEGMENT_PREFIX: ClassVar[str] = "html-class"

    def __init__(self, parent: AttrKeyHTMLClassNode, html_class: str):
        self._value = html_class
        super().__init__(parent)

    def __str__(self) -> str:
        return f"[class: {self._value}]"

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            class_name = unrecovered_attr_value(self._value)
        elif self._is_recovered:
            class_name = self._value
        else:
            return False
        cast(AttributeValueList, item[HTML_CLASS_ATTR_NAME]).append(class_name)
        return True

    @override
    def as_attr_value_html_class_node(self) -> AttrValueHTMLClassNode | None:
        return self

    @override
    def summary_for_recovered_doc(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (count := super().summary_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding html class to SubtreeSummary: {self._value}")
        count.add_html_class(self._value)
        return count

    @override
    def source_summary(self) -> SubtreeSummary:
        return SubtreeSummary.with_html_class(self._value)
