from __future__ import annotations

from typing import TYPE_CHECKING

from star_discovery.bs_helpers import unrecovered_attr_name
from star_discovery.recovery.nodes.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.nodes.attr_value_basic import AttrValueBasicNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.type_aliases import RecoveredKey
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
    from star_discovery.summaries import RevealResult, NodeCount


class AttrKeyBasicNode(AttrKeyBaseNode):
    SEGMENT_PREFIX = "attr-name"

    _attr_value: str
    """Note that this is not the value of this node (that is still the `value`
    attribute in the Node base class. This is instead the corresponding
    value for this attribute, and is just held here to make pushing it
    into the child AttrValueNode node easier (if this node is recovered)."""

    _attr_value_node: AttrValueBasicNode | None

    def __init__(self, parent: HTMLElementBaseNode, attr_key: str, attr_value: str):
        self._attr_value = attr_value
        super().__init__(parent, attr_key)

    def __str__(self) -> str:
        return f"[attr: {self._value}=]"

    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            attr_name = unrecovered_attr_name(self._value)
            item[attr_name] = self._attr_value
            return True
        if self._is_recovered:
            item[self._value] = ""
            if self._attr_value_node:
                self._attr_value_node.add_to_html(item, inc_hidden)
            return True
        return False

    def reveal(self, keys: frozenset[RecoveredKey]) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        self._attr_value_node = AttrValueBasicNode(self, self._attr_value)
        child_node_result = self._attr_value_node.reveal(keys)
        result.merge_in(child_node_result)
        return result

    def as_attr_key_basic_node(self) -> AttrKeyBasicNode | None:
        return self

    def count_for_recovered_doc(self, logger: Logger | None) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding attr to NodeCount: {self._value}")
        count.add_attr_name(self._value)
        if self._attr_value_node:
            if value_count := self._attr_value_node.count_for_recovered_doc(logger):
                count = count.combine(value_count)
        return count
