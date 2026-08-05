from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING

from star_discovery.recovery.abc.base import BaseNode

if TYPE_CHECKING:
    from star_discovery.recovery.types import HTMLParentNode


class AttrKeyBaseNode(BaseNode, ABC):
    """Narrower base class, that captures any HTML attributes except
    for 'class=' which is handled by a different class (this distinction is here
    because we uniquely track class names indecently, all other attribute
    values are tracked verbatim)."""

    _name: str
    _parent: HTMLParentNode

    def __init__(self, parent: HTMLParentNode, attr_key: str):
        self._value = attr_key
        super().__init__(parent)
