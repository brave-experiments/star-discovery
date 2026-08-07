from __future__ import annotations

from typing import override, TYPE_CHECKING

from bs4.element import Tag

from star_discovery.bs_helpers import tag_name
from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
from star_discovery.summaries import NodeCount

if TYPE_CHECKING:
    from bs4 import BeautifulSoup

    from star_discovery.logging import Logger
    from star_discovery.recovery.type_aliases import BSItem


class HTMLElementRootNode(HTMLElementBaseNode):

    @override
    @classmethod
    def count_for_source_item(cls, item: BSItem) -> NodeCount:
        assert isinstance(item, Tag)
        count: NodeCount = NodeCount()
        count.add_html_node(tag_name(item))
        super_count = super(HTMLElementRootNode, cls).count_for_source_item(item)
        return count.combine(super_count)

    def __init__(self, elm: Tag):
        super().__init__(None, elm, 0)

    @override
    def as_html_elm_root_node(self) -> HTMLElementRootNode | None:
        return self

    def recovered_count(self, logger: Logger | None) -> NodeCount | None:
        if not (count := super().count_for_recovered_doc(logger)):
            return None
        return count

    def source_count(self) -> NodeCount:
        return HTMLElementRootNode.count_for_source_item(self._elm)
