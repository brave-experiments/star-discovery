from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override, TYPE_CHECKING
from tempfile import NamedTemporaryFile

from star_discovery.inputs.db import load as load_db

from .abc.base import TestBase

if TYPE_CHECKING:
    from star_discovery.inputs.db import Database


class TestLoadClass(TestBase):

    ASSET_FILES: ClassVar[list[str]] = [
        "cnn_com-JP.html",
        "cnn_com-UK.html",
        "cnn_com-US.html",
    ]

    LOADED_DB: ClassVar[Database]
    NUM_EXPECTED_DOCS: ClassVar[int] = 3

    @override
    @classmethod
    def setup_class(cls) -> None:
        super().setup_class()
        with NamedTemporaryFile() as temp_file:
            temp_file_path = Path(temp_file.name)
            cls.DB.save(temp_file_path, cls.LOGGER)
            cls.LOADED_DB = load_db(temp_file_path)

    def test_num_docs(self) -> None:
        assert len(self.DB.documents()) == len(self.LOADED_DB.documents())

    def test_num_source_nodes(self) -> None:
        docs = self.DB.documents()
        assert len(docs) == self.NUM_EXPECTED_DOCS
        loaded_docs = self.LOADED_DB.documents()
        assert len(loaded_docs) == self.NUM_EXPECTED_DOCS

        for init_doc, loaded_doc in zip(docs, loaded_docs):
            init_summary = init_doc.recovered_summary()
            loaded_summary = loaded_doc.recovered_summary()
            assert init_summary.html_node_count() == loaded_summary.html_node_count()
            assert init_summary.text_node_count() == loaded_summary.text_node_count()
            assert init_summary.attr_name_count() == loaded_summary.attr_name_count()
            assert init_summary.attr_value_count() == loaded_summary.attr_value_count()
