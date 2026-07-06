from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

from star_discovery.inputs.elements import Node




class Document:
    timestamp: datetime
    path: Path
    source: BeautifulSoup

    # Track all leaf nodes that haven't been recovered.  Note
    # that this will grow (for a while) as more of the document is
    # recovered, since initially the entire document is uncovered, and
    # so the "frontier" is the root of the tree.
    frontier_leafs: list[Node] = []


class DocumentCollection:
    input_documents: list[Document] = []

    frontier_leafs: list[Node] = []
