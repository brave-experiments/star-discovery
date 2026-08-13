from __future__ import annotations

from typing import override, TYPE_CHECKING

from bs4.element import AttributeValueList

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


class AttrKeyMultiNode(AttrKeyBaseNode):

    _attr_values: AttributeValueList
    _attr_value_nodes: list[AttrValueNode] | None

    def __init__(
        self,
        parent: HTMLElementBaseNode,
        attr_key: str,
        attr_values: AttributeValueList,
    ):
        self._attr_values = attr_values
        self._attr_value_nodes = None
        super().__init__(parent, attr_key)

    @override
    def as_attr_key_multi_node(self) -> AttrKeyMultiNode | None:
        return self

    @override
    def is_single_value_attr(self) -> bool:
        return False

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            attr_name = unrecovered_attr_name(self._value)
            # pylint: disable-next=consider-using-assignment-expr
            if attr_name in item:
                html_attr = item[attr_name]
                assert isinstance(html_attr, AttributeValueList)
                html_attr += self._attr_values
            else:
                item[attr_name] = self._attr_values
            return True

        if self._is_recovered:
            item[self._value] = AttributeValueList()
            if self._attr_value_nodes:
                for attr_value_node in self._attr_value_nodes:
                    attr_value_node.add_to_html(item, inc_hidden)
            return True
        return False

    @override
    def reveal(self, keys: KeyCollection) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        self._attr_value_nodes = []
        for attr_value in self._attr_values:
            attr_value_node = AttrValueNode(self, attr_value)
            self._attr_value_nodes.append(attr_value_node)
            child_result = attr_value_node.reveal(keys)
            result.merge_in(child_result)
        return result

    @override
    def summary_for_recovered_doc(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (summary := super().summary_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding attr-name to SubtreeSummary: {self._value}")
        summary.add_attr_name(self._value)

        if self._attr_value_nodes:
            for child_node in self._attr_value_nodes:
                if child_summary := child_node.summary_for_recovered_doc(logger):
                    summary += child_summary
        return summary

    @override
    def source_summary(self) -> SubtreeSummary:
        summary = SubtreeSummary.with_attr_name(self._value)
        for attr_value in self._attr_values:
            summary.add_attr_value(attr_value)
        return summary
