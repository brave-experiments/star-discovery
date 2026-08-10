from __future__ import annotations

from abc import ABC
from typing import ClassVar, override, TYPE_CHECKING

from bs4.element import Comment, NavigableString, Tag

from star_discovery.bs_helpers import tag_name, unexpected_elm_error
from star_discovery.recovery.nodes.abc.html_base import HTMLBaseNode
from star_discovery.recovery.nodes.attr_key_basic import AttrKeyBasicNode
from star_discovery.recovery.nodes.attr_key_html_class import AttrKeyHTMLClassNode
from star_discovery.recovery.nodes.html_text import HTMLTextNode
from star_discovery.summaries import NodeCount, RevealResult

if TYPE_CHECKING:
    from bs4.element import AttributeValueList

    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_root import HTMLElementRootNode


HTML_CLASS_ATTR_NAME = "class"


class HTMLElementBaseNode(HTMLBaseNode, ABC):
    SEGMENT_PREFIX: ClassVar[str] = "html"

    _elm: Tag
    _child_nodes: list[HTMLElementBodyNode | HTMLTextNode]
    _basic_attrs: dict[str, AttrKeyBasicNode]
    _html_class_attr: AttrKeyHTMLClassNode | None = None

    _index: int
    """The index of the this HTML element, amongst its peer elements,
    within the parent element."""

    @override
    @classmethod
    def count_for_source_item(cls, item: Tag | NavigableString) -> NodeCount:
        assert isinstance(item, Tag)
        count: NodeCount = NodeCount()

        for attr_name, attr_value in item.attrs.items():
            count.add_attr_name(attr_name)
            if attr_name == HTML_CLASS_ATTR_NAME:
                assert not isinstance(attr_value, str)
                for a_html_class in attr_value:
                    count.add_html_class(a_html_class)
            else:
                assert isinstance(attr_value, str)
                count.add_attr_value(attr_value)

        for child in item.children:
            if isinstance(child, Tag):
                child_count = HTMLElementBodyNode.count_for_source_item(child)
                count = count.combine(child_count)
            elif isinstance(child, NavigableString):
                if trim_text := HTMLTextNode.is_relevant_text(child):
                    child_count = HTMLTextNode.count_for_source_item(trim_text)
                    count = count.combine(child_count)
            else:
                raise unexpected_elm_error(child)
        return count

    def __init__(self, parent: HTMLElementBaseNode | None, elm: Tag, index: int = 0):
        # We should always have a parent recoverable node for an HTML element,
        # unless the node in the HTML document this recoverable node item
        # is tracking does not have a parent (i.e., it is the parent node).
        assert parent or not elm._parent
        self._elm = elm
        self._value = tag_name(elm)
        self._child_nodes = []
        self._basic_attrs = {}
        super().__init__(parent, index)

    def __str__(self) -> str:
        return f"[elm: {self.tag()}]"

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        if self.is_frontier() and inc_hidden:
            child_html = self._elm.prettify()
            comment = Comment(child_html)
            item.append(comment)
            return True

        if self.is_recovered():
            tag = Tag(name=self._elm.name, namespace=self._elm.namespace)
            item.append(tag)

            for child_attr_node in self._basic_attrs.values():
                child_attr_node.add_to_html(tag, inc_hidden)

            if self._html_class_attr:
                self._html_class_attr.add_to_html(tag, inc_hidden)

            for child_node in self._child_nodes:
                child_node.add_to_html(tag, inc_hidden)
            return True

        return False

    @override
    def reveal(self, keys: KeyCollection) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        # Since we've recovered a HTML element node, we potentially have
        # a bunch of new leaf nodes to track, namely a. for each of the
        # just-recovered node's attributes, and b. the just recovered
        # node's child text and child html elements.
        for attr_name, attr_value in self._elm.attrs.items():
            if attr_name == HTML_CLASS_ATTR_NAME:
                assert not isinstance(attr_value, str)
                child_result = self._reveal_attr_key_html_class_node(keys, attr_value)
                result.merge_in(child_result)
                continue
            assert isinstance(attr_value, str)
            child_result = self._reveal_attr_key_basic_node(keys, attr_name, attr_value)
            result.merge_in(child_result)

        index = -1
        for child in self._elm.children:
            if isinstance(child, Tag):
                index += 1
                child_result = self._reveal_html_elm_body_node(keys, child, index)
                result.merge_in(child_result)
            elif isinstance(child, NavigableString):
                if trimmed_text := HTMLTextNode.is_relevant_text(child):
                    index += 1
                    child_result = self._reveal_html_text_node(
                        keys, trimmed_text, index
                    )
                    result.merge_in(child_result)
            else:
                raise unexpected_elm_error(child)
        return result

    @override
    def count_for_recovered_doc(self, logger: Logger | None) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc(logger)):
            return None
        if logger:
            logger.debug(f"adding html node to NodeCount: {tag_name(self._elm)}")
        count.add_html_node(tag_name(self._elm))
        for child in self._child_nodes:
            if child_count := child.count_for_recovered_doc(logger):
                count = count.combine(child_count)
        for basic_attr in self._basic_attrs.values():
            if attr_count := basic_attr.count_for_recovered_doc(logger):
                count = count.combine(attr_count)
        if self._html_class_attr:
            if class_count := self._html_class_attr.count_for_recovered_doc(logger):
                count = count.combine(class_count)
        return count

    def tag(self) -> str:
        return f"<{tag_name(self._elm)}>"

    def _reveal_attr_key_html_class_node(
        self, keys: KeyCollection, html_classes: AttributeValueList
    ) -> RevealResult:
        # We should never see more than one HTML class attribute
        # on a HTML element.
        assert not self._html_class_attr

        html_instance_node = self.as_html_elm_node()
        assert html_instance_node

        html_class_node = AttrKeyHTMLClassNode(html_instance_node, html_classes)
        child_reveal_result = html_class_node.reveal(keys)
        self._html_class_attr = html_class_node
        return child_reveal_result

    def _reveal_attr_key_basic_node(
        self, keys: KeyCollection, attr_name: str, attr_value: str
    ) -> RevealResult:
        assert isinstance(attr_value, str)

        html_instance_node = self.as_html_elm_node()
        assert html_instance_node

        new_attr_node = AttrKeyBasicNode(html_instance_node, attr_name, attr_value)
        self._basic_attrs[attr_name] = new_attr_node
        return new_attr_node.reveal(keys)

    def _reveal_html_elm_body_node(
        self, keys: KeyCollection, elm: Tag, index: int
    ) -> RevealResult:
        html_instance_node = self.as_html_elm_node()
        assert html_instance_node

        child_html_elm = HTMLElementBodyNode(html_instance_node, elm, index)
        self._child_nodes.append(child_html_elm)
        return child_html_elm.reveal(keys)

    def _reveal_html_text_node(
        self, keys: KeyCollection, text: NavigableString, index: int
    ) -> RevealResult:
        html_instance_node = self.as_html_elm_node()
        assert html_instance_node

        child_text_elm = HTMLTextNode(html_instance_node, text, index)
        self._child_nodes.append(child_text_elm)
        return child_text_elm.reveal(keys)


class HTMLElementBodyNode(HTMLElementBaseNode):

    @classmethod
    def count_for_source_item(cls, item: Tag | NavigableString) -> NodeCount:
        assert isinstance(item, Tag)
        count: NodeCount = NodeCount()
        count.add_html_node(tag_name(item))
        super_count = super(HTMLElementBodyNode, cls).count_for_source_item(item)
        return count.combine(super_count)

    def __init__(self, parent: HTMLElementBaseNode, elm: Tag, index: int = 0):
        super().__init__(parent, elm, index)

    @override
    def as_html_elm_body_node(self) -> HTMLElementBodyNode | None:
        return self
