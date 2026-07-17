from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from hashlib import sha256
from typing import ClassVar, TYPE_CHECKING

from star_discovery.documents.input import Document

if TYPE_CHECKING:
    from bs4.element import PageElement as BSPageElement
    from bs4.element import Tag as BSTag
    from bs4.element import NavigableString as BSNavigableString

PATH_SEPARATOR = "|"

# Represents the path to a recoverable element in a input document,
# similar to how a XPATH string describes the path to an item in an XML
# document (though, dramatically simpler).
type NodePathSegment = str
type NodePath = str


# Types of nodes that can have child nodes of any kind
type ParentRecoverableNode = RecoverableHTMLElementNode | RecoverableAttrBasicNode | RecoverableAttrHTMLClassNode


@dataclass
class RecoveryResult:
    html_nodes: list[RecoverableHTMLElementNode] | None = None
    text_nodes: list[RecoverableHTMLTextNode] | None = None
    basic_attr_nodes: list[RecoverableAttrBasicNode] | None = None
    class_attr_node: RecoverableAttrHTMLClassNode | None = None
    attr_value_nodes: list[RecoverableAttrValueNode] | None = None

    def add_html_node(self, node: RecoverableHTMLElementNode) -> None:
        if not self.html_nodes:
            self.html_nodes = []
        self.html_nodes.append(node)

    def add_text_node(self, node: RecoverableHTMLTextNode) -> None:
        if not self.text_nodes:
            self.text_nodes = []
        self.text_nodes.append(node)

    def add_basic_attr_node(self, node: RecoverableAttrBasicNode) -> None:
        if not self.basic_attr_nodes:
            self.basic_attr_nodes = []
        self.basic_attr_nodes.append(node)

    def add_class_attr_node(self, node: RecoverableAttrHTMLClassNode) -> None:
        assert not self.class_attr_node
        self.class_attr_node = node

    def add_attr_value_node(self, node: RecoverableAttrValueNode) -> None:
        if not self.attr_value_nodes:
            self.attr_value_nodes = []
        self.attr_value_nodes.append(node)


# Summary of the class taxonomy for recoverable "things" in STAR-Discovery
# - RecoverableNode (abstract)
#   - RecoverableHTMLNode (abstract)
#     - RecoverableHTMLElementNode
#     - RecoverableHTMLTextNode
#   - RecoverableAttrNode (abstract)
#     - RecoverableAttrBasicNode
#     - RecoverableAttrHTMLClassNode
#   - RecoverableAttrValueNode


class RecoverableNode(ABC):
    """Base class for any kind of thing that is recoverable through the
    STAR-crawl algorithm, so things like HTML tags, text nodes,
    HTML attributes names, HTML attribute values, etc."""

    SEGMENT_PREFIX: ClassVar[str]

    parent: None | ParentRecoverableNode
    value: str
    is_recovered: bool = False
    path: NodePath | None

    def __init__(self, parent: None | ParentRecoverableNode):
        self.is_recovered = False

        # It should never be the case that we're tracking a recoverable node
        # where that parent hasn't already been recovered.
        assert not parent or parent.is_recovered
        self.parent = parent

    def _path_segment_value(self) -> str:
        return self.value

    def _path_segment(self) -> NodePathSegment:
        return self.__class__.SEGMENT_PREFIX + "," + self._path_segment_value()

    def get_path(self) -> NodePath:
        if self.path:
            return self.path
        path_str = self.parent.get_path() if self.parent else PATH_SEPARATOR
        path_str += PATH_SEPARATOR + self._path_segment()
        self.path = path_str
        return path_str

    def recover(self) -> RecoveryResult:
        assert not self.is_recovered
        self.is_recovered = True
        result = RecoveryResult()
        return result

    def as_html_element_node(self) -> RecoverableHTMLElementNode | None:
        return None

    def as_html_text_node(self) -> RecoverableHTMLTextNode | None:
        return None

    def as_attr_basic_node(self) -> RecoverableAttrBasicNode | None:
        return None

    def as_attr_html_class_node(self) -> RecoverableAttrHTMLClassNode | None:
        return None

    def as_attr_value_node(self) -> RecoverableAttrValueNode | None:
        return None


class RecoverableHTMLNode(RecoverableNode, ABC):
    """Narrower base class for recoverable things that map onto Elements
    in HTML documents (HTMLElement, SVGElement, etc) or Text nodes.
    Note this structure is done to mirror BeautifulSoup, and node the HTML
    standard."""

    # The location of this page element (HTML element, text node)
    # amongst its peers within its parent node.
    index: int | None

    def __init__(self, parent: None | RecoverableHTMLElementNode):
        super().__init__(parent)

    def _path_segment_value(self) -> str:
        if self.index:
            return f"{self.index}:{self.value}"
        return self.value


class RecoverableHTMLElementNode(RecoverableHTMLNode):
    SEGMENT_PREFIX = "html"
    element: BSTag
    child_nodes: list[RecoverableHTMLNode] = []
    basic_attrs: dict[str, RecoverableAttrBasicNode] = {}
    html_class_attr: RecoverableAttrHTMLClassNode | None

    # The index of the this HTML element, amongst its peer elements,
    # within the parent element.
    index: int

    def __init__(self, elm: BSTag, parent: None | RecoverableHTMLElementNode):
        # We should always have a parent recoverable node for an HTML element,
        # unless the node in the HTML document this recoverable node item
        # is tracking does not have a parent (i.e., it is the parent node).
        assert parent or not elm.parent
        self.element = elm

        name_bits = elm.namespace or ""
        name_bits += elm.name
        self.value = name_bits
        super().__init__(parent)

    def as_html_element_node(self) -> RecoverableHTMLElementNode | None:
        return self

    def recover(self) -> RecoveryResult:
        result = super().recover()

        # Since we've recovered a HTML element node, we potentially have
        # a bunch of new leaf nodes to track, namely a. for each of the
        # just-recovered node's attributes, and b. the just recovered
        # node's child text and child html elements.
        for attr_name in self.element.attrs.keys():

            if attr_name == "class":
                # We should never see more than one HTML class attribute
                # on a HTML element.
                assert not self.html_class_attr
                self.html_class_attr = RecoverableAttrHTMLClassNode(self)
                result.add_class_attr_node(self.html_class_attr)
                continue

            # Similarly, we should never be tracking the same attribute
            # multiple times on the same HTML element.
            assert attr_name not in self.basic_attrs
            new_attr_node = RecoverableAttrBasicNode(attr_name, self)
            self.basic_attrs[attr_name] = new_attr_node
            result.add_basic_attr_node(new_attr_node)

        for an_elm in self.element.children:
            if isinstance(an_elm, BSTag):
                child_html_elm = RecoverableHTMLElementNode(an_elm, self)
                result.add_html_node(child_html_elm)
            elif isinstance(an_elm, BSNavigableString):
                child_text_elm = RecoverableHTMLTextNode(an_elm, self)
                result.add_text_node(child_text_elm)
            else:
                raise ValueError(
                    f"Unexpected node: [{str(an_elm)}]\n"
                    + f"Parent node is: [{str(self.element)}]"
                )
        return result


class RecoverableHTMLTextNode(RecoverableHTMLNode):
    SEGMENT_PREFIX = "text"
    element: BSNavigableString

    def __init__(self, elm: BSNavigableString, parent: RecoverableHTMLElementNode):
        text_bytes = elm.output_ready().encode("utf8")
        self.value = sha256(text_bytes, usedforsecurity=False).hexdigest()
        self.element = elm
        super().__init__(parent)

    def as_html_text_node(self) -> RecoverableHTMLTextNode | None:
        return self


class RecoverableAttrNode(RecoverableNode, ABC):
    """Narrower base class, that captures any HTML attributes except
    for 'class=' which is handled by a different class (this distinction is here
    because we uniquely track class names indecently, all other attribute
    values are tracked verbatim)."""

    name: str
    parent: RecoverableHTMLElementNode

    def __init__(self, attr_name: str, parent: RecoverableHTMLElementNode):
        self.value = attr_name
        super().__init__(parent)

    def recover(self) -> RecoveryResult:
        return super().recover()


class RecoverableAttrBasicNode(RecoverableAttrNode):
    SEGMENT_PREFIX = "attr-name"

    def __init__(self, attr_name: str, parent: RecoverableHTMLElementNode):
        assert attr_name in parent.basic_attrs
        super().__init__(attr_name, parent)

    def recover(self) -> RecoveryResult:
        result = super().recover()
        attr_value = self.parent.basic_attrs[self.value]
        result.add_attr_value_node(RecoverableAttrValueNode(attr_value, self))
        return result

    def as_attr_basic_node(self) -> RecoverableAttrBasicNode | None:
        return self


class RecoverableAttrHTMLClassNode(RecoverableAttrNode):
    value: list[HTMLAttrValue] = []

    def __init__(self, parent: RecoverableHTMLElementNode):
        assert parent.html_class_attr
        super().__init__("class", parent)

    def recover(self) -> RecoveryResult:
        result = super().recover()
        for html_class_value in self.parent.element.attrs["class"]:
            html_class_value_node = RecoverableAttrValueNode(html_class_value, self)
            result.add_attr_value_node(html_class_value_node)
        return result

    def as_attr_html_class_node(self) -> RecoverableAttrHTMLClassNode | None:
        return self


class RecoverableAttrValueNode(RecoverableNode):
    SEGMENT_PREFIX = "attr-value"

    def __init__(self, attr_value: str, parent: RecoverableAttrNode):
        self.value = attr_value
        super().__init__(parent)

    def recover(self) -> RecoveryResult:
        return super().recover()

    def as_attr_value_node(self) -> RecoverableAttrValueNode | None:
        return self
