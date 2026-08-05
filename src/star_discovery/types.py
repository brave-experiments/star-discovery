from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from star_discovery.recovery.abc.base import BaseNode


# Represents the path to a recoverable element in a input document,
# similar to how a XPATH string describes the path to an item in an XML
# document (though, dramatically simpler).
type NodePathSegment = str
type NodePath = str

type KeyMaterial = NodePath
type RecoveredKey = NodePath
type RecoveredKeys = frozenset[RecoveredKey]


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
    root_nodes: dict[str, int] = field(default_factory=dict)
    html_nodes: dict[str, int] = field(default_factory=dict)
    text_nodes: dict[str, int] = field(default_factory=dict)
    attr_names: dict[str, int] = field(default_factory=dict)
    attr_values: dict[str, int] = field(default_factory=dict)
    html_classes: dict[str, int] = field(default_factory=dict)

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

    def count(self) -> int:
        return (
            NodeCount.sum_dict(self.root_nodes)
            + NodeCount.sum_dict(self.html_nodes)
            + NodeCount.sum_dict(self.text_nodes)
            + NodeCount.sum_dict(self.attr_names)
            + NodeCount.sum_dict(self.attr_values)
            + NodeCount.sum_dict(self.html_classes)
        )

    def add_root_node(self, tag_name: str) -> int:
        return NodeCount.inc_key(self.root_nodes, tag_name)

    def add_html_node(self, tag_name: str) -> int:
        return NodeCount.inc_key(self.html_nodes, tag_name)

    def add_text_node(self, text: str) -> int:
        return NodeCount.inc_key(self.text_nodes, text)

    def add_attr_name(self, attr_name: str) -> int:
        return NodeCount.inc_key(self.attr_names, attr_name)

    def add_attr_value(self, attr_value: str) -> int:
        return NodeCount.inc_key(self.attr_values, attr_value)

    def add_html_class(self, html_class: str) -> int:
        return NodeCount.inc_key(self.html_classes, html_class)

    def combine(self, other: NodeCount) -> NodeCount:
        return NodeCount(
            NodeCount.merge_dicts(self.root_nodes, other.root_nodes),
            NodeCount.merge_dicts(self.html_nodes, other.html_nodes),
            NodeCount.merge_dicts(self.text_nodes, other.text_nodes),
            NodeCount.merge_dicts(self.attr_names, other.attr_names),
            NodeCount.merge_dicts(self.attr_values, other.attr_values),
            NodeCount.merge_dicts(self.html_classes, other.html_classes),
        )
