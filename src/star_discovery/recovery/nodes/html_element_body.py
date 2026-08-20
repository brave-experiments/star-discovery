from __future__ import annotations

from abc import ABC
from typing import override, TYPE_CHECKING

from bs4.element import AttributeValueList, Comment, NavigableString, Tag

from star_discovery.bs_helpers import tag_name, unexpected_elm_error
from star_discovery.recovery.nodes.abc.attr_key_base import AttrKeyBaseNode
from star_discovery.recovery.nodes.abc.html_base import HTMLBaseNode
from star_discovery.recovery.nodes.attr_key_multi import AttrKeyMultiNode
from star_discovery.recovery.nodes.attr_key_single import AttrKeySingleNode
from star_discovery.recovery.nodes.html_text import HTMLTextNode
from star_discovery.summaries import NodeDepth, NodeType, SubtreeSummary, RevealResult

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any, ClassVar

    from bs4 import BeautifulSoup

    from star_discovery.key_store import KeyCollection
    from star_discovery.logging import Logger
    from star_discovery.recovery.nodes.html_element_root import (
        ElmId,
        HTMLElementRootNode,
    )


class HTMLElementBaseNode(HTMLBaseNode, ABC):
    SEGMENT_PREFIX: ClassVar[str] = "html"

    # These values are None-able because they're not stored during pickling;
    # they're None'ed out, and then dynamically recalculated the first time
    # they're needed after being unpickled.
    _root_node: HTMLElementRootNode | None = None
    _elm: Tag | None = None

    _elm_index: ElmId
    """The index of this element in the entire HTML document. Used to
    be able to recover the underlying BeautifulSoup Tag instance, without
    needing to hold a reference to it when pickling."""

    _child_nodes: list[HTMLElementBodyNode | HTMLTextNode]
    _attrs: dict[str, AttrKeyBaseNode]

    _index: int
    """The index of the this HTML element, amongst its peer elements,
    within the parent element."""

    _parent: HTMLElementBaseNode | None

    @classmethod
    def summary_for_source_item(cls, item: Tag) -> SubtreeSummary:
        summary = SubtreeSummary.with_html_node(tag_name(item))
        for attr_name, val in item.attrs.items():
            summary.add_attr_name(attr_name)
            if isinstance(val, AttributeValueList):
                for attr_value in val:
                    summary.add_attr_value(attr_value)
            elif isinstance(val, str):
                summary.add_attr_value(val)
            else:
                assert ValueError(f"Unknown value type: {val}")

        for child in item.children:
            if isinstance(child, Tag):
                summary += HTMLElementBodyNode.summary_for_source_item(child)
            elif isinstance(child, NavigableString):
                if trimmed_text := HTMLTextNode.relevant_text(child):
                    summary.add_text_node(trimmed_text)
            else:
                raise unexpected_elm_error(child)
        return summary

    def __init__(
        self, depth: int, parent: HTMLElementBaseNode | None, elm: Tag, index: int = 0
    ):
        # We should always have a parent recoverable node for an HTML element,
        # unless the node in the HTML document this recoverable node item
        # is tracking does not have a parent (i.e., it is the parent node).
        assert parent or not elm._parent
        self._value = tag_name(elm)
        self._child_nodes = []
        self._attrs = {}
        super().__init__(depth, parent, elm, index)
        self._elm_index = self.get_root_node().index_for_elm(elm)

    def __str__(self) -> str:
        return f"[elm: {self.tag()}]"

    def __getstate__(self) -> dict[str, Any]:
        state = self.__dict__.copy()
        del state["_elm"]
        del state["_root_node"]
        return state

    def get_root_node(self) -> HTMLElementRootNode:
        if self._root_node:
            return self._root_node
        # This assertion is safe because the only case where this will
        # fail (i.e., the only kind of node that does not have a parent)
        # is in the root node, and we override this method in
        # the HTMLElementRootNode class.
        assert self._parent
        self._root_node = self._parent.get_root_node()
        return self._root_node

    def get_elm(self) -> Tag:
        if self._elm:
            return self._elm
        elm = self.get_root_node().elm_for_index(self._elm_index)
        assert elm is not None
        self._elm = elm
        return self._elm

    @override
    def add_to_html(self, item: Tag, inc_hidden: bool = False) -> bool:
        elm = self.get_elm()

        if self.is_frontier() and inc_hidden:
            child_html = elm.prettify()
            comment = Comment(child_html)
            item.append(comment)
            return True

        if self.is_recovered():
            tag = Tag(name=elm.name, namespace=elm.namespace)
            item.append(tag)

            for child_attr_node in self._attrs.values():
                child_attr_node.add_to_html(tag, inc_hidden)

            for child_node in self._child_nodes:
                child_node.add_to_html(tag, inc_hidden)
            return True

        return False

    @override
    def reveal(self, keys: KeyCollection) -> RevealResult:
        success, result = self._reveal_self(keys)
        if not success:
            return result

        elm = self.get_elm()

        # Since we've recovered a HTML element node, we potentially have
        # a bunch of new leaf nodes to track, namely a. for each of the
        # just-recovered node's attributes, and b. the just recovered
        # node's child text and child html elements.
        for attr_name, val in elm.attrs.items():
            if isinstance(val, AttributeValueList):
                child_result = self._reveal_attr_key(keys, attr_name, val)
                result.merge_in(child_result)
            elif isinstance(val, str):
                child_result = self._reveal_attr_key(keys, attr_name, val)
                result.merge_in(child_result)

        index = -1
        for child in elm.children:
            if isinstance(child, Tag):
                index += 1
                child_result = self._reveal_html_elm_body(keys, child, index)
                result.merge_in(child_result)
            elif isinstance(child, NavigableString):
                if HTMLTextNode.relevant_text(child):
                    index += 1
                    child_result = self._reveal_html_text(keys, child, index)
                    result.merge_in(child_result)
            else:
                raise unexpected_elm_error(child)
        return result

    @override
    def summary_for_recovered_doc(self, logger: Logger | None) -> SubtreeSummary | None:
        if not (count := super().summary_for_recovered_doc(logger)):
            return None
        elm = self.get_elm()
        if logger:
            logger.debug(f"adding html node to SubtreeSummary: {tag_name(elm)}")
        count.add_html_node(tag_name(elm))
        for child in self._child_nodes:
            if child_count := child.summary_for_recovered_doc(logger):
                count += child_count
        for attr_key_node in self._attrs.values():
            if attr_count := attr_key_node.summary_for_recovered_doc(logger):
                count += attr_count
        return count

    @override
    def source_summary(self) -> SubtreeSummary:
        return HTMLElementBaseNode.summary_for_source_item(self.get_elm())

    def tag(self) -> str:
        return f"<{tag_name(self.get_elm())}>"

    @override
    def max_depth(self) -> int:
        max_depth = self.depth()
        for child_node in self._child_nodes:
            max_depth = max(max_depth, child_node.max_depth())

        for attr_node in self._attrs.values():
            max_depth = max(max_depth, attr_node.max_depth())
        return max_depth

    def node_depths(self) -> Generator[NodeDepth]:
        if not self.is_recovered():
            return

        yield NodeDepth(self.depth(), NodeType.HTML)
        for child_node in self._child_nodes:
            yield from child_node.node_depths()

        for attr_node in self._attrs.values():
            yield from attr_node.node_depths()

    def _reveal_attr_key(
        self, keys: KeyCollection, attr_key: str, attr_value: AttributeValueList | str
    ) -> RevealResult:
        html_node = self.as_html_elm_node()
        assert html_node

        if isinstance(attr_value, AttributeValueList):
            attr_multi_key_node = AttrKeyMultiNode(
                self.depth() + 1, html_node, attr_key, attr_value
            )
            self._attrs[attr_key] = attr_multi_key_node
            return attr_multi_key_node.reveal(keys)

        attr_single_key_node = AttrKeySingleNode(
            self.depth() + 1, html_node, attr_key, attr_value
        )
        self._attrs[attr_key] = attr_single_key_node
        return attr_single_key_node.reveal(keys)

    def _reveal_html_elm_body(
        self, keys: KeyCollection, elm: Tag, index: int
    ) -> RevealResult:
        html_instance_node = self.as_html_elm_node()
        assert html_instance_node

        child_html_elm = HTMLElementBodyNode(
            self.depth() + 1, html_instance_node, elm, index
        )
        self._child_nodes.append(child_html_elm)
        return child_html_elm.reveal(keys)

    def _reveal_html_text(
        self, keys: KeyCollection, text: NavigableString, index: int
    ) -> RevealResult:
        html_instance_node = self.as_html_elm_node()
        assert html_instance_node

        child_text_elm = HTMLTextNode(self.depth() + 1, html_instance_node, text, index)
        self._child_nodes.append(child_text_elm)
        return child_text_elm.reveal(keys)


class HTMLElementBodyNode(HTMLElementBaseNode):

    def __init__(
        self, depth: int, parent: HTMLElementBaseNode, elm: Tag, index: int = 0
    ):
        super().__init__(depth, parent, elm, index)

    @override
    def as_html_elm_body_node(self) -> HTMLElementBodyNode | None:
        return self
