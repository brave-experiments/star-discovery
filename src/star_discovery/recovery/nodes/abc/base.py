from __future__ import annotations

from abc import ABC
from functools import cached_property
from typing import TYPE_CHECKING

from star_discovery.summaries import NodeCount, RevealResult

if TYPE_CHECKING:
    from typing import ClassVar

    from bs4.element import Tag

    from star_discovery.recovery.nodes.attr_key_basic import AttrKeyBasicNode
    from star_discovery.recovery.nodes.attr_key_html_class import AttrKeyHTMLClassNode
    from star_discovery.recovery.nodes.attr_value_basic import AttrValueBasicNode
    from star_discovery.recovery.nodes.attr_value_html_class import (
        AttrValueHTMLClassNode,
    )
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBodyNode
    from star_discovery.recovery.nodes.html_element_root import HTMLElementRootNode
    from star_discovery.recovery.nodes.html_text import HTMLTextNode
    from star_discovery.recovery.type_aliases import (
        ChildHavingNode,
        KeyMaterial,
        RecoveredKey,
        RevealResultSelf,
    )


PATH_SEPARATOR = "|"


class BaseNode(ABC):
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

    def __str__(self) -> str:
        raise NotImplementedError()

    def is_frontier(self) -> bool:
        is_root_or_recovered_parent = not self._parent or self._parent.is_recovered()
        return is_root_or_recovered_parent and not self.is_recovered()

    def is_recovered(self) -> bool:
        return self._is_recovered

    def add_to_html(self, item: Tag) -> bool:
        raise NotImplementedError()

    def reveal(self, keys: frozenset[RecoveredKey]) -> RevealResult:
        _, result = self._reveal_self(keys)
        return result

    @cached_property
    def path(self) -> KeyMaterial:
        path_str = self._parent.path if self._parent else PATH_SEPARATOR
        path_str += PATH_SEPARATOR + self._path_segment()
        return path_str

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

    def count_for_recovered_doc(self) -> NodeCount | None:
        if not self._is_recovered:
            return None
        return NodeCount()

    def _path_segment_value(self) -> str:
        return self._value

    def _path_segment(self) -> str:
        return self.__class__.SEGMENT_PREFIX + "," + self._path_segment_value()

    def _reveal_self(self, keys: frozenset[RecoveredKey]) -> RevealResultSelf:
        assert not self._is_recovered
        if self.path not in keys:
            return False, RevealResult.from_frontier(self)
        self._is_recovered = True
        return True, RevealResult.from_recovered(self)
