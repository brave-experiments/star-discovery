from __future__ import annotations

from typing import override, TYPE_CHECKING

from star_discovery.bs_helpers import unrecovered_attr_name
from star_discovery.recovery.nodes.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.nodes.attr_value import AttrValueNode
from star_discovery.summaries import SubtreeSummary

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
    from star_discovery.summaries import RevealResult


class AttrKeySingleNode(AttrKeyBaseNode):

    _attr_value: str
    _attr_value_node: AttrValueNode | None

    def __init__(self, parent: HTMLElementBaseNode, attr_key: str, attr_value: str):
        self._attr_value = attr_value
        self._attr_value_node = None
        super().__init__(parent, attr_key)

    @override
    def as_attr_key_single_node(self) -> AttrKeySingleNode | None:
        return self

    @override
    def is_single_value_attr(self) -> bool:
        return True

    @override
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

    @override
    def reveal(self, keys: KeyCollection) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        self._attr_value_node = AttrValueNode(self, self._attr_value)
        child_result = self._attr_value_node.reveal(keys)
        result.merge_in(child_result)
        return result

    @override
    def summary_for_recovered_doc(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (summary := super().summary_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding attr-name to SubtreeSummary: {self._value}")
        summary.add_attr_name(self._value)

        if self._attr_value_node:
            if child_summary := self._attr_value_node.summary_for_recovered_doc(logger):
                summary += child_summary
        return summary

    @override
    def source_summary(self) -> SubtreeSummary:
        summary = SubtreeSummary.with_attr_name(self._value)
        summary.add_attr_value(self._attr_value)
        return summary
