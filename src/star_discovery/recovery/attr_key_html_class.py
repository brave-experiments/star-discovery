from __future__ import annotations

from typing import TYPE_CHECKING

from bs4.element import AttributeValueList

from star_discovery.recovery.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.attr_value_html_class import AttrValueHTMLClassNode
from star_discovery.types import NodeCount

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.recovery.types import BSItem, HTMLParentNode
    from star_discovery.types import RecoveredKeys, RevealResult


HTML_CLASS_ATTR_NAME = "class"


class AttrKeyHTMLClassNode(AttrKeyBaseNode):
    SEGMENT_PREFIX = "attr-class"

    _html_classes: list[str]
    """Note that these HTML class names are not the value being protected
    by this class/instance, but instead just being held here so they
    can be propagated to into AttrValueNode instances (one for each
    class name) if this current `AttrHTMLClassNode` instance is recovered."""

    _html_class_nodes: list[AttrValueHTMLClassNode] | None

    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, str)
        count: NodeCount = NodeCount()
        count.add_attr_name(HTML_CLASS_ATTR_NAME)
        return count

    def __init__(self, parent: HTMLParentNode, html_classes: list[str]):
        self._html_classes = html_classes
        super().__init__(parent, HTML_CLASS_ATTR_NAME)

    def __str__(self) -> str:
        return "[class=]"

    def add_to_html(self, item: Tag) -> bool:
        if not self._is_recovered:
            return False
        item["class"] = AttributeValueList()
        if self._html_class_nodes:
            for html_class_node in self._html_class_nodes:
                html_class_node.add_to_html(item)
        return True

    def reveal(self, keys: RecoveredKeys) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        self._html_class_nodes = []
        for html_class in self._html_classes:
            child_node = AttrValueHTMLClassNode(self, html_class)
            self._html_class_nodes.append(child_node)
            result.merge_in(child_node.reveal(keys))
        return result

    def as_attr_key_html_class_node(self) -> AttrKeyHTMLClassNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None

        count.add_attr_value(HTML_CLASS_ATTR_NAME)
        if not self._html_class_nodes:
            return count

        for html_class_node in self._html_class_nodes:
            if html_class_count := html_class_node.count_for_recovered_doc():
                count.combine(html_class_count)
        return count
