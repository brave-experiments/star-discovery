from __future__ import annotations

from abc import ABC
from functools import cached_property
from typing import ClassVar, TYPE_CHECKING

from star_discovery.key_store import NodeTag
from star_discovery.summaries import SubtreeSummary, RevealResult

if TYPE_CHECKING:
    from bs4.element import Tag, NavigableString

    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.abc.attr_key_base import (
        AttrKeyBaseNode,
    )
    from star_discovery.recovery.nodes.attr_key_basic import AttrKeyBasicNode
    from star_discovery.recovery.nodes.attr_key_html_class import AttrKeyHTMLClassNode
    from star_discovery.recovery.nodes.attr_value_basic import AttrValueBasicNode
    from star_discovery.recovery.nodes.attr_value_html_class import (
        AttrValueHTMLClassNode,
    )
    from star_discovery.recovery.nodes.html_element_body import (
        HTMLElementBaseNode,
        HTMLElementBodyNode,
    )
    from star_discovery.recovery.nodes.html_element_root import HTMLElementRootNode
    from star_discovery.recovery.nodes.html_text import HTMLTextNode


PATH_SEPARATOR = "|"

type RevealResultSelf = tuple[bool, RevealResult]


class BaseNode(ABC):
    """Base class for any kind of thing that is recoverable through the
    STAR-crawl algorithm, so things like HTML tags, text nodes,
    HTML attributes names, HTML attribute values, etc."""

    SEGMENT_PREFIX: ClassVar[str]

    _is_recovered: bool = False
    _parent: HTMLElementBaseNode | AttrKeyBaseNode | None
    _value: str

    @classmethod
    def summary_for_source_item(cls, item: Tag) -> SubtreeSummary:
        raise NotImplementedError("summary_for_source_item", cls)

    def __init__(self, parent: HTMLElementBaseNode | AttrKeyBaseNode | None):
        self._is_recovered = False

        # It should never be the case that we're tracking a recoverable node
        # where that parent hasn't already been recovered.
        assert not parent or parent._is_recovered
        self._parent = parent

    def is_frontier(self) -> bool:
        is_root_or_recovered_parent = not self._parent or self._parent.is_recovered()
        return is_root_or_recovered_parent and not self.is_recovered()

    def is_recovered(self) -> bool:
        return self._is_recovered

    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        raise NotImplementedError("add_to_html", self)

    def reveal(self, keys: KeyCollection) -> RevealResult:
        _, result = self._reveal_self(keys)
        return result

    def source_summary(self) -> SubtreeSummary:
        raise NotImplementedError("source_summary", self)

    @cached_property
    def node_tag(self) -> NodeTag:
        path_str = self._parent.node_tag if self._parent else PATH_SEPARATOR
        path_str += PATH_SEPARATOR + self._path_segment()
        return NodeTag(path_str)

    def as_html_elm_root_node(self) -> HTMLElementRootNode | None:
        return None

    def as_html_elm_body_node(self) -> HTMLElementBodyNode | None:
        return None

    def as_html_elm_node(self) -> HTMLElementRootNode | HTMLElementBodyNode | None:
        return self.as_html_elm_root_node() or self.as_html_elm_body_node()

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

    # pylint: disable-next=unused-argument
    def summary_for_recovered_doc(self, logger: Logger | None) -> SubtreeSummary | None:
        if not self._is_recovered:
            return None
        return SubtreeSummary()

    def _path_segment_value(self) -> str:
        return self._value

    def _path_segment(self) -> str:
        return f"({self.__class__.SEGMENT_PREFIX})-{self._path_segment_value()}"

    def _reveal_self(self, keys: KeyCollection) -> RevealResultSelf:
        assert not self._is_recovered
        if self.node_tag not in keys:
            return False, RevealResult.from_frontier(self)
        self._is_recovered = True
        return True, RevealResult.from_recovered(self)
