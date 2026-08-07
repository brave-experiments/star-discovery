"""A collection of very light classes (mostly dataclasses) uses for summarizing
changes and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
    from star_discovery.recovery.nodes.abc.base import BaseNode


def desc_some_nodes(nodes: set[BaseNode], num_items: int) -> str:
    items_to_show = (str(x) for x in list(nodes)[:num_items])
    items_full_desc = ", ".join(items_to_show)
    num_recovered = len(nodes)
    hidden_items = num_recovered - num_items

    if hidden_items <= 0:
        return items_full_desc
    if hidden_items == 1:
        return f"{items_full_desc} and 1 more node"
    return f"{items_full_desc} and {hidden_items} more nodes"


@dataclass
class RevealResult:
    recovered: set[BaseNode] = field(default_factory=set)
    frontier: set[BaseNode] = field(default_factory=set)

    @staticmethod
    def from_recovered(node: BaseNode) -> RevealResult:
        result = RevealResult()
        result.recovered.add(node)
        return result

    @staticmethod
    def from_frontier(node: BaseNode) -> RevealResult:
        result = RevealResult()
        result.frontier.add(node)
        return result

    def __str__(self) -> str:
        return f"recovered: {self.desc_recovered()}, frontier: {self.desc_frontier()}"

    def desc_recovered(self, show_items: int = 3) -> str:
        return desc_some_nodes(self.recovered, show_items)

    def desc_frontier(self, show_items: int = 3) -> str:
        return desc_some_nodes(self.frontier, show_items)

    def merge_in(self, other: RevealResult) -> None:
        self.recovered |= other.recovered
        self.frontier |= other.frontier


@dataclass
class NodeCount:
    _html_nodes_key: ClassVar[str] = "html_nodes"
    _text_nodes_key: ClassVar[str] = "text_nodes"
    _attr_names_key: ClassVar[str] = "attr_names"
    _attr_values_key: ClassVar[str] = "attr_values"
    _html_classes_key: ClassVar[str] = "html_classes"

    html_nodes: dict[str, int] = field(default_factory=dict)
    text_nodes: dict[str, int] = field(default_factory=dict)
    attr_names: dict[str, int] = field(default_factory=dict)
    attr_values: dict[str, int] = field(default_factory=dict)
    html_classes: dict[str, int] = field(default_factory=dict)
    _cache: dict[str, int | None] = field(default_factory=dict, init=False)

    @staticmethod
    def inc_key(data: dict[str, int], key: str) -> int:
        try:
            data[key] += 1
        except KeyError:
            data[key] = 1
        return data[key]

    @staticmethod
    def merge_dicts(*dicts: dict[str, int]) -> dict[str, int]:
        union_dict: dict[str, int] = {}
        for a_dict in dicts:
            for key, value in a_dict.items():
                try:
                    union_dict[key] += value
                except KeyError:
                    union_dict[key] = value
        return union_dict

    @staticmethod
    def sum_dict(data: dict[str, int]) -> int:
        return sum(data.values())

    def __post_init__(self) -> None:
        self._cache = {
            NodeCount._html_nodes_key: None,
            NodeCount._text_nodes_key: None,
            NodeCount._attr_names_key: None,
            NodeCount._attr_values_key: None,
            NodeCount._html_classes_key: None,
        }

    def total(self) -> int:
        return (
            self.html_node_count()
            + self.text_node_count()
            + self.attr_name_count()
            + self.attr_value_count()
            + self.html_class_count()
        )

    def add_html_node(self, tag_name: str) -> int:
        self._cache[NodeCount._html_nodes_key] = None
        return NodeCount.inc_key(self.html_nodes, tag_name)

    def html_node_count(self) -> int:
        if (cached_value := self._cache[NodeCount._html_nodes_key]) is not None:
            return cached_value
        value = NodeCount.sum_dict(self.html_nodes)
        self._cache[NodeCount._html_nodes_key] = value
        return value

    def add_text_node(self, text: str) -> int:
        self._cache[NodeCount._text_nodes_key] = None
        return NodeCount.inc_key(self.text_nodes, text)

    def text_node_count(self) -> int:
        if (cached_value := self._cache[NodeCount._text_nodes_key]) is not None:
            return cached_value
        value = NodeCount.sum_dict(self.text_nodes)
        self._cache[NodeCount._text_nodes_key] = value
        return value

    def add_attr_name(self, attr_name: str) -> int:
        self._cache[NodeCount._attr_names_key] = None
        return NodeCount.inc_key(self.attr_names, attr_name)

    def attr_name_count(self) -> int:
        if (cached_value := self._cache[NodeCount._attr_names_key]) is not None:
            return cached_value
        value = NodeCount.sum_dict(self.attr_names)
        self._cache[NodeCount._attr_names_key] = value
        return value

    def add_attr_value(self, attr_value: str) -> int:
        self._cache[NodeCount._attr_values_key] = None
        return NodeCount.inc_key(self.attr_values, attr_value)

    def attr_value_count(self) -> int:
        if (cached_value := self._cache[NodeCount._attr_values_key]) is not None:
            return cached_value
        value = NodeCount.sum_dict(self.attr_values)
        self._cache[NodeCount._attr_values_key] = value
        return value

    def add_html_class(self, html_class: str) -> int:
        self._cache[NodeCount._html_classes_key] = None
        return NodeCount.inc_key(self.html_classes, html_class)

    def html_class_count(self) -> int:
        if (cached_value := self._cache[NodeCount._html_classes_key]) is not None:
            return cached_value
        value = NodeCount.sum_dict(self.html_classes)
        self._cache[NodeCount._html_classes_key] = value
        return value

    def combine(self, other: NodeCount) -> NodeCount:
        return NodeCount(
            NodeCount.merge_dicts(self.html_nodes, other.html_nodes),
            NodeCount.merge_dicts(self.text_nodes, other.text_nodes),
            NodeCount.merge_dicts(self.attr_names, other.attr_names),
            NodeCount.merge_dicts(self.attr_values, other.attr_values),
            NodeCount.merge_dicts(self.html_classes, other.html_classes),
        )
