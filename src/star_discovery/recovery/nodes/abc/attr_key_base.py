from __future__ import annotations

from abc import ABC
from typing import ClassVar, override, TYPE_CHECKING

from star_discovery.recovery.nodes.abc.base import BaseNode

if TYPE_CHECKING:
    from collections.abc import Generator

    from bs4.element import Tag

    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
    from star_discovery.summaries import NodeDepth, RevealResult


class AttrKeyBaseNode(BaseNode, ABC):
    SEGMENT_PREFIX: ClassVar[str] = "attr-name"

    def __init__(self, depth: int, parent: HTMLElementBaseNode, attr_key: str):
        self._value = attr_key
        super().__init__(depth, parent)

    def __str__(self) -> str:
        return f"[attr: {self._value}=]"

    @override
    def as_attr_key_node(self) -> AttrKeyBaseNode | None:
        return self

    def max_depth(self) -> int:
        raise NotImplementedError("max_depth", self)

    def is_single_value_attr(self) -> bool:
        raise NotImplementedError("is_single_value_attr", self)

    def node_depths(self) -> Generator[NodeDepth]:
        raise NotImplementedError("node_depths", self)
