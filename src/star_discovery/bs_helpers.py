from __future__ import annotations

from typing import cast, TYPE_CHECKING

from bs4.element import AttributeValueList, NavigableString, Tag

from star_discovery.summaries import (
    DepthSummary,
    NodeDepth,
    NodeType,
    NodeTypeCount,
)

if TYPE_CHECKING:
    from typing import Any
    from collections.abc import Generator

    from bs4 import BeautifulSoup

MINIMUM_TITLE_LEN = 5


def get_root_node(html: BeautifulSoup) -> Tag:
    if html_node := html.find("html"):
        return html_node
    raise ValueError(f"Could not find a root <html> node in document: {html}")


def html_desc(html: BeautifulSoup, additional_desc: str | None = None) -> str:
    # See if we can get a title out of the beautiful soup file
    desc: str = ""
    if title_tag := html.find("title"):
        title_text = title_tag.get_text().strip()
        if len(title_text) >= MINIMUM_TITLE_LEN:
            desc = title_text

    if additional_desc:
        desc += " - " + additional_desc
    return desc


def _max(first: NodeDepth, second: NodeDepth) -> NodeDepth:
    if first.depth < second.depth:
        return second
    return first


def _max_depth(tag: Tag, depth: int) -> NodeDepth:
    local_max = NodeDepth(depth, NodeType.HTML)
    for child in tag.children:
        if isinstance(child, NavigableString) and len(child.strip()) > 0:
            local_max = _max(NodeDepth(depth + 1, NodeType.TEXT), local_max)
        elif isinstance(child, Tag):
            local_max = _max(_max_depth(child, depth + 1), local_max)

    for attr_name, attr_value in tag.attrs.items():
        local_max = _max(NodeDepth(depth + 1, NodeType.NAME), local_max)
        if isinstance(attr_value, NavigableString):
            local_max = _max(NodeDepth(depth + 2, NodeType.VALUE), local_max)
        elif isinstance(attr_value, AttributeValueList):
            for a_value in attr_value:
                local_max = _max(NodeDepth(depth + 2, NodeType.VALUE), local_max)
                # Early break here because all the values will have the same
                # depth, and so need to iterate over all of them (since that'd
                # just end up emitting identical values).
                break
    return local_max


def max_depth(html: BeautifulSoup) -> NodeDepth:
    return _max_depth(get_root_node(html), 0)


def _node_depths(tag: Tag, depth: int) -> Generator[NodeDepth]:
    yield NodeDepth(depth, NodeType.HTML)

    for child in tag.children:
        if isinstance(child, NavigableString) and len(child.strip()) > 0:
            yield NodeDepth(depth + 1, NodeType.TEXT)
        elif isinstance(child, Tag):
            yield from _node_depths(child, depth + 1)

    for attr_name, attr_value in tag.attrs.items():
        # We don't call `.items()` here because we dont actually care about
        # specific attribute names here, just the number of attribute names
        # (and the number of corresponding values).
        yield NodeDepth(depth + 1, NodeType.NAME)
        if isinstance(attr_value, str):
            yield NodeDepth(depth + 2, NodeType.VALUE)
        elif isinstance(attr_value, AttributeValueList):
            for a_value in attr_value:
                yield NodeDepth(depth + 2, NodeType.VALUE)


def node_depths(html: BeautifulSoup) -> Generator[NodeDepth]:
    yield from _node_depths(get_root_node(html), 0)


def depth_summary(html: BeautifulSoup) -> DepthSummary:
    """Return a dictionary describing the different counts of node types,
    for each depth of node in the document. So, if
    `result = node_depth_summary(html)`, then `print(result[2][NodeType.HTML])`
    would print a count for the number of HTML nodes in the document that
    are children of the children of the root node."""
    summary: dict[int, NodeTypeCount] = {}
    for depth_info in node_depths(html):
        if depth_info.depth not in summary:
            summary[depth_info.depth] = NodeTypeCount()
        summary[depth_info.depth].inc(depth_info.node_type)

    flat_summary: list[NodeTypeCount | None] = list([None] * len(summary))
    for key, value in summary.items():
        flat_summary[key] = value
    return cast(DepthSummary, flat_summary)


def unrecovered_attr_name(attr_name: str) -> str:
    return f"-@sd-{attr_name}"


def unrecovered_attr_value(attr_value: str) -> str:
    return f"@sd-{attr_value}"


def tag_name(elm: Tag) -> str:
    if elm.namespace:
        return f"{elm.namespace}:{elm.name}"
    return elm.name


def unexpected_elm_error(elm: Any, index: None | int = 0) -> ValueError:
    return ValueError(
        f"Unexpected node: [{str(elm)}] (index: {index})\n"
        + f"Parent node is: [{str(elm.parent)}]"
    )
