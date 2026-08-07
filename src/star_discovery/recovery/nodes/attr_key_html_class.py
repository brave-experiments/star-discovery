from __future__ import annotations

from typing import ClassVar, override, TYPE_CHECKING

from bs4.element import AttributeValueList

from star_discovery.bs_helpers import unrecovered_attr_name
from star_discovery.recovery.nodes.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.nodes.attr_value_html_class import AttrValueHTMLClassNode
from star_discovery.summaries import NodeCount

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
    from star_discovery.recovery.type_aliases import BSItem, RecoveredKey
    from star_discovery.summaries import RevealResult


HTML_CLASS_ATTR_NAME = "class"


class AttrKeyHTMLClassNode(AttrKeyBaseNode):
    SEGMENT_PREFIX: ClassVar[str] = "attr-class"

    _html_classes: list[str]
    """Note that these HTML class names are not the value being protected
    by this class/instance, but instead just being held here so they
    can be propagated to into AttrValueNode instances (one for each
    class name) if this current `AttrHTMLClassNode` instance is recovered."""

    _html_class_nodes: list[AttrValueHTMLClassNode] | None

    @override
    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, str)
        count: NodeCount = NodeCount()
        count.add_attr_name(HTML_CLASS_ATTR_NAME)
        return count

    def __init__(self, parent: HTMLElementBaseNode, html_classes: list[str]):
        self._html_classes = html_classes
        super().__init__(parent, HTML_CLASS_ATTR_NAME)

    def __str__(self) -> str:
        return "[class=]"

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            attr_name = unrecovered_attr_name(HTML_CLASS_ATTR_NAME)
            item[attr_name] = AttributeValueList(self._html_classes)
            return True
        if self._is_recovered:
            item["class"] = AttributeValueList()
            if self._html_class_nodes:
                for html_class_node in self._html_class_nodes:
                    html_class_node.add_to_html(item, inc_hidden)
            return True
        return False

    @override
    def reveal(self, keys: frozenset[RecoveredKey]) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        self._html_class_nodes = []
        for html_class in self._html_classes:
            child_node = AttrValueHTMLClassNode(self, html_class)
            self._html_class_nodes.append(child_node)
            result.merge_in(child_node.reveal(keys))
        return result

    @override
    def as_attr_key_html_class_node(self) -> AttrKeyHTMLClassNode | None:
        return self

    @override
    def count_for_recovered_doc(self, logger: Logger | None) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding attr to NodeCount: {HTML_CLASS_ATTR_NAME}")
        count.add_attr_name(HTML_CLASS_ATTR_NAME)
        if not self._html_class_nodes:
            return count
        for html_class_node in self._html_class_nodes:
            if html_class_count := html_class_node.count_for_recovered_doc(logger):
                count = count.combine(html_class_count)
        return count
