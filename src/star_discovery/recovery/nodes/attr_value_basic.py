from __future__ import annotations

from typing import ClassVar, override, TYPE_CHECKING

from star_discovery.bs_helpers import unrecovered_attr_value
from star_discovery.recovery.nodes.abc.base import BaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.attr_key_basic import AttrKeyBasicNode
    from star_discovery.summaries import NodeCount


class AttrValueBasicNode(BaseNode):
    SEGMENT_PREFIX: ClassVar[str] = "attr-value"

    _attr_name: str

    def __init__(self, parent: AttrKeyBasicNode, attr_value: str):
        self._attr_name = parent._value
        self._value = attr_value
        super().__init__(parent)

    def __str__(self) -> str:
        return f"[attr: ={self._value}]"

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            attr_value = unrecovered_attr_value(self._value)
            item[self._attr_name] = attr_value
            return True
        if self._is_recovered:
            attr_value = self._value
            item[self._attr_name] = attr_value
            return True
        return False

    @override
    def as_attr_value_basic_node(self) -> AttrValueBasicNode | None:
        return self

    @override
    def count_for_recovered_doc(self, logger: Logger | None) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding attr value to NodeCount: {self._value}")
        count.add_attr_value(self._value)
        return count
