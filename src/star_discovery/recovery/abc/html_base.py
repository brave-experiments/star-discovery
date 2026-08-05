from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from star_discovery.recovery.abc.base import BaseNode

if TYPE_CHECKING:
    from star_discovery.recovery.types import HTMLParentNode


class HTMLBaseNode(BaseNode, ABC):
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
