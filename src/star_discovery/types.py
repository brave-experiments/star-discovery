from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from star_discovery.documents.recovered import Node


# Represents the path to a recoverable element in a input document,
# similar to how a XPATH string describes the path to an item in an XML
# document (though, dramatically simpler).
type NodePathSegment = str
type NodePath = str

type KeyMaterial = NodePath
type RecoveredKey = NodePath
type RecoveredKeys = frozenset[RecoveredKey]


@dataclass
class RevealResult:
    recovered: set[Node] = set()
    frontier: set[Node] = set()

    @staticmethod
    def from_recovered(node: Node) -> RevealResult:
        result = RevealResult()
        result.recovered.add(node)
        return result

    @staticmethod
    def from_frontier(node: Node) -> RevealResult:
        result = RevealResult()
        result.frontier.add(node)
        return result

    def merge_in(self, other: RevealResult) -> None:
        self.recovered |= other.recovered
        self.frontier |= other.frontier


@dataclass
class NodeCount:
    root_nodes: dict[str, int] = {}
    html_nodes: dict[str, int] = {}
    text_nodes: dict[str, int] = {}
    attr_names: dict[str, int] = {}
    attr_values: dict[str, int] = {}
    html_classes: dict[str, int] = {}

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
