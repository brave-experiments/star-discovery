"""A collection of very light classes (mostly dataclasses) uses for summarizing
changes and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Final, Literal
    from star_discovery.recovery.nodes.abc.base import BaseNode


type NodeTrackingDict = dict[str, int]


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


type DictKey = str


@dataclass
class DictDifference:
    key: DictKey
    source: int
    comparison: Literal[">" | "<"]
    revealed: int
    hidden: int
    total: int = field(init=False)

    def __post_init__(self) -> None:
        self.total = abs(self.source - (self.revealed + self.hidden))
        if self.total == 0:
            raise ValueError(
                f"Values do not depict a difference. source={self.source} == "
                f"(revealed={self.revealed} + hidden={self.hidden})"
            )


def diff_keys_in_dict(dict1: NodeTrackingDict, dict2: NodeTrackingDict) -> list[str]:
    differences: list[str] = []
    for key, dict1_value in dict1.items():
        if key not in dict2:
            differences.append(key)
            continue

        dict2_value = dict2[key]
        if dict1_value != dict2_value:
            differences.append(key)
            continue

    for key, dict2_value in dict2.items():
        if key not in dict1:
            differences.append(key)
    return differences


def describe_diff_for_key(
    key: DictKey,
    source: NodeTrackingDict,
    revealed: NodeTrackingDict,
    hidden: NodeTrackingDict,
) -> DictDifference:
    source_count = source.get(key, 0)
    revealed_count = revealed.get(key, 0)
    hidden_count = hidden.get(key, 0)
    source_is_bigger = source_count > (revealed_count + hidden_count)

    return DictDifference(
        key,
        source_count,
        ">" if source_is_bigger else "<",
        revealed_count,
        hidden_count,
    )


def compare_summaries(
    source: SubtreeSummary,
    revealed: SubtreeSummary,
    hidden: SubtreeSummary,
) -> list[tuple[str, DictDifference]]:
    all_differences: list[tuple[str, DictDifference]] = []
    combined = revealed + hidden

    def _get_diffs(summary_key: DictKey) -> list[tuple[str, DictDifference]]:
        local_diffs: list[tuple[str, DictDifference]] = []

        source_dict = cast(NodeTrackingDict, getattr(source, summary_key))
        combined_dict = cast(NodeTrackingDict, getattr(combined, summary_key))
        revealed_dict = cast(NodeTrackingDict, getattr(revealed, summary_key))
        hidden_dict = cast(NodeTrackingDict, getattr(hidden, summary_key))

        for key_with_diff in diff_keys_in_dict(source_dict, combined_dict):
            a_diff = describe_diff_for_key(
                key_with_diff,
                source_dict,
                revealed_dict,
                hidden_dict,
            )
            local_diffs.append((summary_key, a_diff))

        return local_diffs

    all_differences += _get_diffs("html_nodes")
    all_differences += _get_diffs("text_nodes")
    all_differences += _get_diffs("attr_names")
    all_differences += _get_diffs("attr_values")

    return all_differences


HTML_NODES_KEY: Final[str] = "html_nodes"
TEXT_NODES_KEY: Final[str] = "text_nodes"
ATTR_NAMES_KEY: Final[str] = "attr_names"
ATTR_VALUES_KEY: Final[str] = "attr_values"


@dataclass
class SubtreeSummary:
    html_nodes: NodeTrackingDict = field(default_factory=dict)
    text_nodes: NodeTrackingDict = field(default_factory=dict)
    attr_names: NodeTrackingDict = field(default_factory=dict)
    attr_values: NodeTrackingDict = field(default_factory=dict)

    _cache: dict[str, int | None] = field(
        default_factory=dict, init=False, compare=False
    )

    @staticmethod
    def with_html_node(item: str) -> SubtreeSummary:
        summary = SubtreeSummary()
        summary.add_html_node(item)
        return summary

    @staticmethod
    def with_text_node(item: str) -> SubtreeSummary:
        summary = SubtreeSummary()
        summary.add_text_node(item)
        return summary

    @staticmethod
    def with_attr_name(item: str) -> SubtreeSummary:
        summary = SubtreeSummary()
        summary.add_attr_name(item)
        return summary

    @staticmethod
    def with_attr_value(item: str) -> SubtreeSummary:
        summary = SubtreeSummary()
        summary.add_attr_value(item)
        return summary

    @staticmethod
    def inc_key(data: NodeTrackingDict, key: str) -> int:
        try:
            data[key] += 1
        except KeyError:
            data[key] = 1
        return data[key]

    @staticmethod
    def merge_dicts(*dicts: NodeTrackingDict) -> NodeTrackingDict:
        union_dict: NodeTrackingDict = {}
        for a_dict in dicts:
            for key, value in a_dict.items():
                try:
                    union_dict[key] += value
                except KeyError:
                    union_dict[key] = value
        return union_dict

    @staticmethod
    def sum_dict(data: NodeTrackingDict) -> int:
        return sum(data.values())

    def __post_init__(self) -> None:
        self._cache = {
            HTML_NODES_KEY: None,
            TEXT_NODES_KEY: None,
            ATTR_NAMES_KEY: None,
            ATTR_VALUES_KEY: None,
        }

    def __hash__(self) -> int:
        return hash(
            (
                self.html_nodes,
                self.text_nodes,
                self.attr_names,
                self.attr_values,
            )
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, SubtreeSummary):
            return False
        return (
            self.html_nodes == other.html_nodes
            and self.text_nodes == other.text_nodes
            and self.attr_names == other.attr_names
            and self.attr_values == other.attr_values
        )

    def __add__(self, other: Any) -> SubtreeSummary:
        if not isinstance(other, SubtreeSummary):
            raise ValueError(f"object {other} is not a SubtreeSummary instance")
        return SubtreeSummary(
            html_nodes=SubtreeSummary.merge_dicts(self.html_nodes, other.html_nodes),
            text_nodes=SubtreeSummary.merge_dicts(self.text_nodes, other.text_nodes),
            attr_names=SubtreeSummary.merge_dicts(self.attr_names, other.attr_names),
            attr_values=SubtreeSummary.merge_dicts(self.attr_values, other.attr_values),
        )

    def to_jsonable(self) -> dict[str, NodeTrackingDict]:
        return {
            "html_nodes": self.html_nodes,
            "text_nodes": self.text_nodes,
            "attr_names": self.attr_names,
            "attr_values": self.attr_values,
        }

    def total(self) -> int:
        return (
            self.html_node_count()
            + self.text_node_count()
            + self.attr_name_count()
            + self.attr_value_count()
        )

    def add_html_node(self, tag_name: str) -> int:
        self._cache[HTML_NODES_KEY] = None
        return SubtreeSummary.inc_key(self.html_nodes, tag_name)

    def html_node_count(self) -> int:
        if (cached_value := self._cache[HTML_NODES_KEY]) is not None:
            return cached_value
        value = SubtreeSummary.sum_dict(self.html_nodes)
        self._cache[HTML_NODES_KEY] = value
        return value

    def add_text_node(self, text: str) -> int:
        self._cache[TEXT_NODES_KEY] = None
        return SubtreeSummary.inc_key(self.text_nodes, text)

    def text_node_count(self) -> int:
        if (cached_value := self._cache[TEXT_NODES_KEY]) is not None:
            return cached_value
        value = SubtreeSummary.sum_dict(self.text_nodes)
        self._cache[TEXT_NODES_KEY] = value
        return value

    def add_attr_name(self, attr_name: str) -> int:
        self._cache[ATTR_NAMES_KEY] = None
        return SubtreeSummary.inc_key(self.attr_names, attr_name)

    def attr_name_count(self) -> int:
        if (cached_value := self._cache[ATTR_NAMES_KEY]) is not None:
            return cached_value
        value = SubtreeSummary.sum_dict(self.attr_names)
        self._cache[ATTR_NAMES_KEY] = value
        return value

    def add_attr_value(self, attr_value: str) -> int:
        self._cache[ATTR_VALUES_KEY] = None
        return SubtreeSummary.inc_key(self.attr_values, attr_value)

    def attr_value_count(self) -> int:
        if (cached_value := self._cache[ATTR_VALUES_KEY]) is not None:
            return cached_value
        value = SubtreeSummary.sum_dict(self.attr_values)
        self._cache[ATTR_VALUES_KEY] = value
        return value
