from __future__ import annotations

from typing import NewType, TYPE_CHECKING

if TYPE_CHECKING:
    from star_discovery.inputs.document import Document


NodeTag = NewType("NodeTag", str)
RecoveredKey = NewType("RecoveredKey", NodeTag)
type KeyCollection = frozenset[RecoveredKey]


class KeyStore:
    _key_contributions: dict[NodeTag, set[Document]]
    _recovered_keys: set[RecoveredKey]
    _threshold: int

    def __init__(self, threshold: int):
        self._threshold = threshold
        self._key_contributions = {}
        self._recovered_keys = set()

    def recovered_keys(self) -> KeyCollection:
        return frozenset(self._recovered_keys)

    def add_key_share(self, doc: Document, key_share: NodeTag) -> bool:
        contributing_docs: set[Document] | None = None
        try:
            contributing_docs = self._key_contributions[key_share]
        except KeyError:
            contributing_docs = set()

        contributing_docs.add(doc)
        self._key_contributions[key_share] = contributing_docs
        if is_key_recovered := len(contributing_docs) >= self._threshold:
            self._recovered_keys.add(RecoveredKey(key_share))
        return is_key_recovered
