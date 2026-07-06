from __future__ import annotations

from abc import ABC
from hashlib import sha256
from typing import ClassVar, TYPE_CHECKING

from star_discovery.inputs.document import Document

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

# Summary of the class taxonomy for recoverable "things" in STAR-Discovery
# - Node (abstract)
#   - PageElement (abstract)
#     - HTMLElement
#     - Text
#   - HTMLAttrBase (abstract)
#     - HTMLAttr
#     - HTMLClass
#   - HTMLAttrValue

class Node(ABC):
    """Base class for any kind of thing that is recoverable through the
    STAR-crawl algorithm, so things like HTML tags, text nodes,
    HTML attributes names, HTML attribute values, etc."""

    SEGMENT_PREFIX: ClassVar[str]

    document: Document
    path: NodePath | None
    parent: HTMLElement | HTMLAttrBase | None
    value: str

    def __init__(self, doc: Document):
        self.document = doc

    def path_segment(self) -> NodePathSegment:
        return self.__class__.SEGMENT_PREFIX + "," + self.value

    def get_path(self) -> NodePath:
        if self.path:
            return self.path
        path_str = self.parent.get_path() if self.parent else PATH_SEPARATOR
        path_str += PATH_SEPARATOR + self.path_segment()
        self.path = path_str
        return path_str


class PageElement(Node, ABC):
    """Narrower base class for recoverable things that map onto Elements
    in HTML documents (HTMLElement, SVGElement, etc) or Text nodes.
    Note this structure is done to mirror BeautifulSoup, and node the HTML
    standard."""

    element: BSPageElement

    def __init__(self, doc: Document, elm: BSPageElement):
        self.element = elm
        super().__init__(doc)


class HTMLElement(PageElement):

    SEGMENT_PREFIX = "html"

    # The index of the this HTML element, amongst its peer elements,
    # within the parent element.
    index: int

    def __init__(self, doc: Document, elm: BSTag):
        name_bits = elm.namespace or ""
        name_bits += elm.name
        self.value = name_bits
        super().__init__(doc, elm)


class Text(PageElement):
    SEGMENT_PREFIX = "text"

    def __init__(self, doc: Document, elm: BSNavigableString):
        text_bytes = elm.output_ready().encode("utf8")
        self.value = sha256(text_bytes, usedforsecurity=False).hexdigest()
        super().__init__(doc, elm)


class HTMLAttrBase(Node, ABC):
    """Narrower base class, that captures any HTML attributes except
    for 'class=' which is handled by a different class (this distinction is here
    because we uniquely track class names indecently, all other attribute
    values are tracked verbatim)."""

    name: str
    value: HTMLAttrValue | list[HTMLAttrValue]

    def __init__(self, doc: Document, attr_name: str):
        self.value = attr_name
        super().__init__(doc)


class HTMLAttr(HTMLAttrBase):
    SEGMENT_PREFIX = "attr-name"

    value: HTMLAttrValue


class HTMLClass(HTMLAttrBase):
    value: list[HTMLAttrValue] = []

    def __init__(self, doc: Document):
        super().__init__(doc, "class")


class HTMLAttrValue(Node):
    SEGMENT_PREFIX = "attr-value"

    def __init__(self, doc: Document, attr_value: str):
        self.value = attr_value
        super().__init__(doc)
