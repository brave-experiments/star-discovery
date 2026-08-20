from __future__ import annotations

from typing import override, TYPE_CHECKING

from bs4.element import AttributeValueList

from star_discovery.bs_helpers import unrecovered_attr_value
from star_discovery.recovery.nodes.abc.base import BaseNode
from star_discovery.summaries import NodeDepth, NodeType, SubtreeSummary

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import ClassVar

    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.abc.attr_key_base import AttrKeyBaseNode


class AttrValueNode(BaseNode):
    SEGMENT_PREFIX: ClassVar[str] = "attr-value"
    _parent: AttrKeyBaseNode
    _has_been_depthed: bool = False

    def __init__(self, depth: int, parent: AttrKeyBaseNode, attr_value: str):
        self._attr_name = parent._value
        self._value = attr_value
        super().__init__(depth, parent)

    def __str__(self) -> str:
        return f"[attr: ={self._value}]"

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            unrecovered_value = unrecovered_attr_value(self._value)
            if self.is_single_value_attr():
                item[self._attr_name] = unrecovered_value
            elif self._attr_name in item:
                attr_list = item[self._attr_name]
                assert isinstance(attr_list, AttributeValueList)
                attr_list.append(unrecovered_value)
            else:
                item[self._attr_name] = AttributeValueList((unrecovered_value,))
            return True

        if self._is_recovered:
            if self.is_single_value_attr():
                item[self._attr_name] = self._value
            elif self._attr_name in item:
                attr_list = item[self._attr_name]
                assert isinstance(attr_list, AttributeValueList)
                attr_list.append(self._value)
            else:
                item[self._attr_name] = AttributeValueList((self._value,))
            return True

        return False

    @override
    def summary_for_recovered_doc(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (count := super().summary_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding attr value to SubtreeSummary: {self._value}")
        count.add_attr_value(self._value)
        return count

    @override
    def source_summary(self) -> SubtreeSummary:
        return SubtreeSummary.with_attr_value(self._value)

    def is_single_value_attr(self) -> bool:
        return self._parent.is_single_value_attr()

    def node_depths(self) -> Generator[NodeDepth]:
        if not self.is_recovered():
            return
        yield NodeDepth(self.depth(), NodeType.VALUE)
