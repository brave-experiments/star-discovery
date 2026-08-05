from __future__ import annotations

from typing import TYPE_CHECKING

from star_discovery.recovery.abc.base import BaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.recovery.attr_key_basic import AttrKeyBasicNode
    from star_discovery.types import NodeCount


class AttrValueBasicNode(BaseNode):
    SEGMENT_PREFIX = "attr-value"

    _attr_name: str

    def __init__(self, parent: AttrKeyBasicNode, attr_value: str):
        self._attr_name = parent._value
        self._value = attr_value
        super().__init__(parent)

    def __str__(self) -> str:
        return f"[attr: ={self._value}]"

    def add_to_html(self, item: Tag) -> bool:
        if not self._is_recovered:
            return False
        item[self._attr_name] = self._value
        return True

    def as_attr_value_basic_node(self) -> AttrValueBasicNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_attr_value(self._value)
        return count
