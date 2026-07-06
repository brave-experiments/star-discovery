from __future__ import annotations

from pathlib import Path
import pickle
from typing import ClassVar

from star_discovery.database.input import InputDocument


class StarDiscoveryDatabase:
    DEFAULT_FILENAME: ClassVar[str] = "star-discovery.database"

    inputs: list[InputDocument] = []

    @classmethod
    def load(cls, path: Path) -> StarDiscoveryDatabase | None:
        with path.open("b") as handle:
            data = pickle.load(handle)
            if isinstance(data, StarDiscoveryDatabase):
                return data
        return None

    @classmethod
    def create(cls, path: Path) -> StarDiscoveryDatabase | None:
        with path.open("wb") as handle:
            new_db = StarDiscoveryDatabase()
            pickle.dump(new_db, handle)
            return new_db
        return None
