from __future__ import annotations

from abc import ABC
from functools import cached_property
from hashlib import sha256
from typing import ClassVar, TYPE_CHECKING

from bs4.element import AttributeValueList as BSAttributeValueList
from bs4.element import NavigableString as BSString
from bs4.element import Tag as BSTag

from star_discovery.bs_helpers import tag_name, unexpected_elm_error
from star_discovery.types import NodeCount, RevealResult

if TYPE_CHECKING:
    from star_discovery.types import NodePath, NodePathSegment
    from star_discovery.types import RecoveredKey, RecoveredKeys


PATH_SEPARATOR = "|"
HTML_CLASS_ATTR_NAME = "class"


type ChildHavingNode = HTMLElementBaseNode | AttrKeyBaseNode
"""Types of nodes that can have child nodes of any kind."""

type HTMLParentNode = HTMLElementRootNode | HTMLElementBodyNode
"""Types of nodes that can be parents to HTMLNode instances."""

type RevealResultSelf = tuple[bool, RevealResult]
type HTMLClasses = BSAttributeValueList

type BSItem = BSTag | BSString | str


# Summary of the class taxonomy for recoverable "things" in STAR-Discovery
# - Node (abstract)
#   - HTMLNode (abstract)
#     - HTMLElementBaseNode (abstract)
#       - HTMLElementRootNode
#       - HTMLElementBodyNode
#     - HTMLTextNode
#   - AttrKeyBaseNode (abstract)
#     - AttrKeyBasicNode
#     - AttrKeyHTMLClassNode
#   - AttrValueBasicNode
#   - AttrValueHTMLClassNode
class Node(ABC):
    """Base class for any kind of thing that is recoverable through the
    STAR-crawl algorithm, so things like HTML tags, text nodes,
    HTML attributes names, HTML attribute values, etc."""

    SEGMENT_PREFIX: ClassVar[str]

    _is_recovered: bool = False
    _parent: ChildHavingNode | None
    _value: str

    def __init__(self, parent: ChildHavingNode | None):
        self._is_recovered = False

        # It should never be the case that we're tracking a recoverable node
        # where that parent hasn't already been recovered.
        assert not parent or parent._is_recovered
        self._parent = parent

    def _path_segment_value(self) -> str:
        return self._value

    def _path_segment(self) -> NodePathSegment:
        return self.__class__.SEGMENT_PREFIX + "," + self._path_segment_value()

    def _reveal_self(self, keys: RecoveredKeys) -> RevealResultSelf:
        assert not self._is_recovered
        if self.path not in keys:
            return False, RevealResult.from_frontier(self)
        self._is_recovered = True
        return True, RevealResult.from_recovered(self)

    def reveal(self, keys: RecoveredKeys) -> RevealResult:
        _, result = self._reveal_self(keys)
        return result

    @cached_property
    def path(self) -> NodePath:
        path_str = self._parent.path if self._parent else PATH_SEPARATOR
        path_str += PATH_SEPARATOR + self._path_segment()
        return path_str

    def as_html_elm_root_node(self) -> HTMLElementRootNode | None:
        return None

    def as_html_elm_body_node(self) -> HTMLElementBodyNode | None:
        return None

    def as_html_text_node(self) -> HTMLTextNode | None:
        return None

    def as_attr_key_basic_node(self) -> AttrKeyBasicNode | None:
        return None

    def as_attr_key_html_class_node(self) -> AttrKeyHTMLClassNode | None:
        return None

    def as_attr_value_basic_node(self) -> AttrValueBasicNode | None:
        return None

    def as_attr_value_html_class_node(self) -> AttrValueHTMLClassNode | None:
        return None

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not self._is_recovered:
            return None
        return NodeCount()


class HTMLNode(Node, ABC):
    """Narrower base class for recoverable things that map onto Elements
    in HTML documents (HTMLElement, SVGElement, etc) or Text nodes.
    Note this structure is done to mirror BeautifulSoup, and node the HTML
    standard."""

    _index: int | None
    """The location of this page element (HTML element, text node)
    amongst its peers within its parent node."""

    def __init__(self, parent: HTMLParentNode | None, index: int = 0):
        self._index = index
        super().__init__(parent)

    def _path_segment_value(self) -> str:
        if self._index:
            return f"{self._index}:{self._value}"
        return self._value


class HTMLElementBaseNode(HTMLNode, ABC):
    SEGMENT_PREFIX = "html"

    _elm: BSTag
    _child_nodes: list[HTMLElementBodyNode | HTMLTextNode] = []
    _basic_attrs: dict[str, AttrKeyBasicNode] = {}
    _html_class_attr: AttrKeyHTMLClassNode | None

    _index: int
    """The index of the this HTML element, amongst its peer elements,
    within the parent element."""

    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, BSTag)
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
            if isinstance(child, BSTag):
                child_count = HTMLElementBodyNode.count_for_source_item(child)
                count = count.combine(child_count)
            elif isinstance(child, BSString):
                child_count = HTMLTextNode.count_for_source_item(child)
                count = count.combine(child_count)
            else:
                raise unexpected_elm_error(child)
        return count

    def __init__(self, parent: HTMLParentNode | None, elm: BSTag, index: int = 0):
        # We should always have a parent recoverable node for an HTML element,
        # unless the node in the HTML document this recoverable node item
        # is tracking does not have a parent (i.e., it is the parent node).
        assert parent or not elm._parent
        self._elm = elm
        self._value = tag_name(elm)
        super().__init__(parent, index)

    def reveal(self, keys: RecoveredKeys) -> RevealResult:
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

        elm_index = -1
        for an_elm in self._elm.children:
            elm_index += 1
            if isinstance(an_elm, BSTag):
                child_result = self._reveal_html_elm_body_node(keys, an_elm, elm_index)
                result.merge_in(child_result)
            elif isinstance(an_elm, BSString):
                child_result = self._reveal_html_text_node(keys, an_elm, elm_index)
                result.merge_in(child_result)
            else:
                raise unexpected_elm_error(an_elm)
        return result

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        for child in self._child_nodes:
            if child_count := child.count_for_recovered_doc():
                count = count.combine(child_count)
        for basic_attr in self._basic_attrs.values():
            if attr_count := basic_attr.count_for_recovered_doc():
                count = count.combine(attr_count)
        if self._html_class_attr:
            if class_count := self._html_class_attr.count_for_recovered_doc():
                count = count.combine(class_count)
        return count

    def _reveal_attr_key_html_class_node(
        self, keys: RecoveredKeys, html_classes: HTMLClasses
    ) -> RevealResult:
        # We should never see more than one HTML class attribute
        # on a HTML element.
        assert not self._html_class_attr
        assert isinstance(self, HTMLElementRootNode | HTMLElementBodyNode)
        html_class_node = AttrKeyHTMLClassNode(self, html_classes)
        child_reveal_result = html_class_node.reveal(keys)
        self._html_class_attr = html_class_node
        return child_reveal_result

    def _reveal_attr_key_basic_node(
        self, keys: RecoveredKeys, attr_name: str, attr_value: str
    ) -> RevealResult:
        # we should never be tracking the same attribute
        # multiple times on the same HTML element.
        assert attr_name not in self._basic_attrs
        assert isinstance(attr_value, str)
        assert isinstance(self, HTMLElementRootNode | HTMLElementBodyNode)
        new_attr_node = AttrKeyBasicNode(self, attr_name, attr_value)
        self._basic_attrs[attr_name] = new_attr_node
        return new_attr_node.reveal(keys)

    def _reveal_html_elm_body_node(
        self, keys: RecoveredKeys, elm: BSTag, index: int
    ) -> RevealResult:
        assert isinstance(self, HTMLElementRootNode | HTMLElementBodyNode)
        child_html_elm = HTMLElementBodyNode(self, elm, index)
        self._child_nodes.append(child_html_elm)
        return child_html_elm.reveal(keys)

    def _reveal_html_text_node(
        self, keys: RecoveredKeys, text: BSString, index: int
    ) -> RevealResult:
        assert isinstance(self, HTMLElementRootNode | HTMLElementBodyNode)
        child_text_elm = HTMLTextNode(self, text, index)
        self._child_nodes.append(child_text_elm)
        return child_text_elm.reveal(keys)


class HTMLElementRootNode(HTMLElementBaseNode):

    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, BSTag)
        count: NodeCount = NodeCount()
        count.add_root_node(tag_name(item))
        super_count = super(HTMLElementRootNode, cls).count_for_source_item(item)
        return count.combine(super_count)

    def __init__(self, elm: BSTag):
        super().__init__(None, elm, 0)

    def as_html_elm_root_node(self) -> HTMLElementRootNode | None:
        return self

    @cached_property
    def source_count(self) -> NodeCount:
        return HTMLElementRootNode.count_for_source_item(self._elm)

    def recovered_count(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_root_node(tag_name(self._elm))
        return count


class HTMLElementBodyNode(HTMLElementBaseNode):

    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, BSTag)
        count: NodeCount = NodeCount()
        count.add_html_node(tag_name(item))
        super_count = super(HTMLElementBodyNode, cls).count_for_source_item(item)
        return count.combine(super_count)

    def __init__(self, parent: HTMLParentNode, elm: BSTag, index: int = 0):
        super().__init__(parent, elm, index)

    def as_html_elm_body_node(self) -> HTMLElementBodyNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_html_node(tag_name(self._elm))
        return count


class HTMLTextNode(HTMLNode):
    SEGMENT_PREFIX = "text"

    _elm: BSString

    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, BSString)
        count: NodeCount = NodeCount()
        count.add_text_node(item)
        return count

    def __init__(self, parent: HTMLParentNode, elm: BSString, index: int):
        text_bytes = elm.output_ready().encode("utf8")
        self.value = sha256(text_bytes, usedforsecurity=False).hexdigest()
        self._elm = elm
        super().__init__(parent, index)

    def as_html_text_node(self) -> HTMLTextNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_text_node(self._elm)
        return count


class AttrKeyBaseNode(Node, ABC):
    """Narrower base class, that captures any HTML attributes except
    for 'class=' which is handled by a different class (this distinction is here
    because we uniquely track class names indecently, all other attribute
    values are tracked verbatim)."""

    _name: str
    _parent: HTMLParentNode

    def __init__(self, parent: HTMLParentNode, attr_key: str):
        self._value = attr_key
        super().__init__(parent)


class AttrKeyBasicNode(AttrKeyBaseNode):
    SEGMENT_PREFIX = "attr-name"

    _attr_value: str
    """Note that this is not the value of this node (that is still the `value`
    attribute in the Node base class. This is instead the corresponding
    value for this attribute, and is just held here to make pushing it
    into the child AttrValueNode node easier (if this node is recovered)."""

    _attr_value_node: AttrValueBasicNode | None

    def __init__(self, parent: HTMLParentNode, attr_key: str, attr_value: str):
        assert attr_key in parent._basic_attrs
        self._attr_value = attr_value
        super().__init__(parent, attr_key)

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


class AttrKeyHTMLClassNode(AttrKeyBaseNode):

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
        assert parent._html_class_attr
        self._html_classes = html_classes
        super().__init__(parent, HTML_CLASS_ATTR_NAME)

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


class AttrValueBasicNode(Node):
    SEGMENT_PREFIX = "attr-value"

    def __init__(self, parent: AttrKeyBasicNode, attr_value: str):
        self._value = attr_value
        super().__init__(parent)

    def as_attr_value_basic_node(self) -> AttrValueBasicNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_attr_value(self._value)
        return count


class AttrValueHTMLClassNode(Node):
    SEGMENT_PREFIX = "html-class"

    def __init__(self, parent: AttrKeyHTMLClassNode, html_class: str):
        self._value = html_class
        super().__init__(parent)

    def as_attr_value_html_class_node(self) -> AttrValueHTMLClassNode | None:
        return self

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc()):
            return None
        count.add_attr_value(self._value)
        return count
