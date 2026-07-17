from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

from star_discovery.documents.recovered import (
    RecoverableNode,
    RecoverableHTMLElementNode,
    NodePath,
)

if TYPE_CHECKING:
    from bs4.element import Tag as BSTag


class Document:
    name: str
    bs_doc: BeautifulSoup
    timestamp: datetime
    root_node: RecoverableHTMLElementNode

    # Track all leaf nodes that haven't been recovered.  Note
    # that this will grow (for a while) as more of the document is
    # recovered, since initially the entire document is uncovered, and
    # so the "frontier" is the root of the tree.
    frontier_nodes: dict[NodePath, list[RecoverableNode]] = {}

    # This is just here for asserting and testing, to make sure we never see
    # a node path again, once its been completed.
    prev_revealed_paths: set[NodePath] = {}

    def __init__(self, bs_doc: BeautifulSoup, name: str):
        self.bs_doc = bs_doc
        self.name = name
        self.timestamp = datetime.now()

        root_tag_name = self.bs_doc.ROOT_TAG_NAME
        root_tag = self.bs_doc.find(root_tag_name, recursive=False)
        assert root_tag is not None

        self.root_node = RecoverableHTMLElementNode(self, root_tag)
        self.frontier_nodes[self.root_node.get_path] = [self.root_node]

    def add_frontier_nodes(self, nodes: list[RecoverableNode]):
        # Depending on how strictly or loosely we consider nodes to be
        # equivalent, its possible different nodes will have the same
        # path (i.e., whether we treat two <divs> with the same immediate
        # parent node as equivalent). But, even in the laxest cases, we should
        # never see the same path in different lists of nodes (i.e., all paths
        # should be unique to groups of nodes revealed in the document at the
        # same time).
        assert node_path not in self.frontier_nodes
        self.frontier_nodes[node_path] = node

    def reveal_nodes_at_path(self, node_path: NodePath) -> int:
        assert node_path not in self.prev_revealed_paths
        self.prev_revealed_paths.add(node_path)

        if node_path not in self.frontier_nodes:
            return 0
        recovered_nodes = self.frontier_nodes.pop(node_path)
        num_recovered_nodes = len(recovered_nodes)

        for a_recovered_node in recovered_nodes:
            new_child_nodes = self.recover_node()

    def recover_node(self, node: RecoverableNode) -> None:
        assert node in self.frontier_nodes
        assert not node.is_recovered


class DocumentCollection:
    input_documents: list[Document] = []

    def add_input_document(self, bs_doc: BeautifulSoup, path: Path) -> None:
        new_document = Document()
