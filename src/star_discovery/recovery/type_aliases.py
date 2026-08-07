from __future__ import annotations

from bs4.element import AttributeValueList, NavigableString, Tag

from star_discovery.summaries import RevealResult
from star_discovery.recovery.nodes.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.nodes.html_element_body import HTMLElementBaseNode

type ChildHavingNode = HTMLElementBaseNode | AttrKeyBaseNode
"""Types of nodes that can have child nodes of any kind."""

type RevealResultSelf = tuple[bool, RevealResult]
type HTMLClasses = AttributeValueList

type BSItem = Tag | NavigableString

# Represents the path to a recoverable element in a input document,
# similar to how a XPATH string describes the path to an item in an XML
# document (though, dramatically simpler).
type KeyMaterial = str
type RecoveredKey = KeyMaterial
