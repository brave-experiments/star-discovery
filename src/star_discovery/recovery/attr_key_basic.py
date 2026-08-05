from __future__ import annotations

from typing import TYPE_CHECKING

from star_discovery.recovery.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.attr_value_basic import AttrValueBasicNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.types import RecoveredKeys, RevealResult, NodeCount
    from star_discovery.recovery.types import HTMLParentNode


class AttrKeyBasicNode(AttrKeyBaseNode):
    SEGMENT_PREFIX = "attr-name"

    _attr_value: str
    """Note that this is not the value of this node (that is still the `value`
    attribute in the Node base class. This is instead the corresponding
    value for this attribute, and is just held here to make pushing it
    into the child AttrValueNode node easier (if this node is recovered)."""

    _attr_value_node: AttrValueBasicNode | None

    def __init__(self, parent: HTMLParentNode, attr_key: str, attr_value: str):
        self._attr_value = attr_value
        super().__init__(parent, attr_key)

    def __str__(self) -> str:
        return f"[attr: {self._value}=]"

    def add_to_html(self, item: Tag) -> bool:
        if not self._is_recovered:
            return False
        item[self._value] = ""
        if self._attr_value_node:
            self._attr_value_node.add_to_html(item)
        return True

    def reveal(self, keys: RecoveredKeys) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        self._attr_value_node = AttrValueBasicNode(self, self._attr_value)
        child_node_result = self._attr_value_node.reveal(keys)
        result.merge_in(child_node_result)
        return result

    def as_attr_key_basic_node(self) -> AttrKeyBasicNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None

        count.add_attr_name(self._value)
        if not self._attr_value_node:
            return count

        if value_count := self._attr_value_node.count_for_recovered_doc():
            count.combine(value_count)
        return count
