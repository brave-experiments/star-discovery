from __future__ import annotations

from typing import override, TYPE_CHECKING

from bs4.element import Tag

from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
from star_discovery.summaries import SubtreeSummary

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    from bs4.element import NavigableString

    from star_discovery.logging import Logger


class HTMLElementRootNode(HTMLElementBaseNode):

    def __init__(self, elm: Tag):
        super().__init__(None, elm, 0)

    @override
    def as_html_elm_root_node(self) -> HTMLElementRootNode | None:
        return self

    def recovered_summary(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (count := super().summary_for_recovered_doc(logger)):
            return None
        return count
