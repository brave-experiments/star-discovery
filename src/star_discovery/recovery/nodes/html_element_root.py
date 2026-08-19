from __future__ import annotations

from typing import Any, cast, NewType, override, TYPE_CHECKING

from bs4.element import Tag

from star_discovery.bs_helpers import depth_summary, max_depth
from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
from star_discovery.summaries import DepthSummary, NodeTypeCount, SubtreeSummary

if TYPE_CHECKING:
    from bs4 import BeautifulSoup
    from bs4.element import NavigableString

    from star_discovery.logging import Logger


ElmId = NewType("ElmId", int)
type TagToIndexCache = dict[Tag, int]
type IndexToTagCache = dict[int, Tag]


class HTMLElementRootNode(HTMLElementBaseNode):

    # These values are None-able because they're not stored during pickling;
    # they're None'ed out, and then dynamically recalculated the first time
    # they're needed after being unpickled.
    _tag_to_index_cache: TagToIndexCache | None = None
    _index_to_tag_cache: IndexToTagCache | None = None

    _html: BeautifulSoup

    _root_node: None = None

    def __init__(self, html: BeautifulSoup):
        self._html = html
        elm = html.find("html")
        assert elm is not None
        super().__init__(0, None, elm, 0)

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        del state["_elm"]
        del state["_index_to_tag_cache"]
        del state["_tag_to_index_cache"]
        return state

    @override
    def as_html_elm_root_node(self) -> HTMLElementRootNode | None:
        return self

    @override
    def get_root_node(self) -> HTMLElementRootNode:
        return self

    def get_tag_to_index_cache(self) -> TagToIndexCache:
        if self._tag_to_index_cache is not None:
            return self._tag_to_index_cache
        self._generate_caches()
        assert self._tag_to_index_cache is not None
        return self._tag_to_index_cache

    def get_index_to_tag_cache(self) -> IndexToTagCache:
        if self._index_to_tag_cache is not None:
            return self._index_to_tag_cache
        self._generate_caches()
        assert self._index_to_tag_cache is not None
        return self._index_to_tag_cache

    def index_for_elm(self, elm: Tag) -> ElmId:
        elm_index = self.get_tag_to_index_cache().get(elm)
        assert elm_index is not None
        return ElmId(elm_index)

    def elm_for_index(self, index: ElmId) -> Tag:
        elm = self.get_index_to_tag_cache().get(index)
        assert elm is not None
        return elm

    def recovered_summary(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (count := super().summary_for_recovered_doc(logger)):
            return None
        return count

    def source_depth(self) -> int:
        return max_depth(self._html).depth

    def recovery_depth(self) -> int:
        return self.max_depth()

    def source_depths_summary(self) -> DepthSummary:
        return depth_summary(self._html)

    def recovered_depths_summary(self) -> DepthSummary:
        summary: dict[int, NodeTypeCount] = {}
        for node_depth in self.node_depths():
            if node_depth.depth not in summary:
                summary[node_depth.depth] = NodeTypeCount()
            summary[node_depth.depth].inc(node_depth.node_type)

        flat_summary: list[NodeTypeCount | None] = list([None] * len(summary))
        for key, value in summary.items():
            flat_summary[key] = value
        return cast(DepthSummary, flat_summary)

    def _generate_caches(self) -> None:
        self._tag_to_index_cache = {}
        self._index_to_tag_cache = {}
        index = 0
        for elm in self._html.descendants:
            if isinstance(elm, Tag):
                self._tag_to_index_cache[elm] = index
                self._index_to_tag_cache[index] = elm
                index += 1
