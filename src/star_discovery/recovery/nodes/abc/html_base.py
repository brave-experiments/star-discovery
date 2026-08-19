from __future__ import annotations

from abc import ABC
from typing import override, TYPE_CHECKING

from star_discovery.recovery.nodes.abc.base import BaseNode

if TYPE_CHECKING:
    from bs4.element import NavigableString, Tag

    from star_discovery.summaries import SubtreeSummary
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode


class HTMLBaseNode(BaseNode, ABC):
    """Narrower base class for recoverable things that map onto Elements
    in HTML documents (HTMLElement, SVGElement, etc) or Text nodes.
    Note this structure is done to mirror BeautifulSoup, and node the HTML
    standard."""

    _index: int | None
    """The location of this page element (HTML element, text node)
    amongst its peers within its parent node."""

    _elm: NavigableString | Tag | None

    def __init__(
        self,
        depth: int,
        parent: HTMLElementBaseNode | None,
        elm: NavigableString | Tag,
        index: int = 0,
    ):
        self._elm = elm
        self._index = index
        super().__init__(depth, parent)

    @override
    def _path_segment_value(self) -> str:
        if self._index:
            return f"{self._index}:{self._value}"
        return self._value

    def max_depth(self) -> int:
        raise NotImplementedError("max_depth", self)
