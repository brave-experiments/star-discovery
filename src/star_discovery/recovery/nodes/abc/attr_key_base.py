from __future__ import annotations

from abc import ABC
from typing import ClassVar, override, TYPE_CHECKING

from star_discovery.recovery.nodes.abc.base import BaseNode

if TYPE_CHECKING:
    from bs4.element import Tag

    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode
    from star_discovery.summaries import RevealResult


class AttrKeyBaseNode(BaseNode, ABC):
    SEGMENT_PREFIX: ClassVar[str] = "attr-name"

    def __init__(self, parent: HTMLElementBaseNode, attr_key: str):
        self._value = attr_key
        super().__init__(parent)

    def __str__(self) -> str:
        return f"[attr: {self._value}=]"

    @override
    def as_attr_key_node(self) -> AttrKeyBaseNode | None:
        return self

    def is_single_value_attr(self) -> bool:
        raise NotImplementedError("is_single_value_attr", self)
