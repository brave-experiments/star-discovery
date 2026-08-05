from __future__ import annotations

from bs4.element import AttributeValueList, NavigableString, Tag

from star_discovery.types import RevealResult
from star_discovery.recovery.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.html_element_body import (
    HTMLElementBaseNode,
    HTMLElementBodyNode,
)
from star_discovery.recovery.html_element_root import HTMLElementRootNode

type ChildHavingNode = HTMLElementBaseNode | AttrKeyBaseNode
"""Types of nodes that can have child nodes of any kind."""

type HTMLParentNode = HTMLElementRootNode | HTMLElementBodyNode
"""Types of nodes that can be parents to HTMLNode instances."""

type RevealResultSelf = tuple[bool, RevealResult]
type HTMLClasses = AttributeValueList

type BSItem = Tag | NavigableString
