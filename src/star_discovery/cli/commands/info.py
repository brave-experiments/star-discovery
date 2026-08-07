from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import json
from typing import Any, Literal, Final, TYPE_CHECKING

from tabulate import tabulate

from star_discovery.cli.commands.common import (
    CommonArgs,
    add_db_arg,
    add_logging_args,
    validate as common_validate,
)

if TYPE_CHECKING:
    from star_discovery.inputs.db import Database
    from star_discovery.inputs.document import Document, RecoverySummary

SUBCOMMAND_NAME = "info"
FORMAT_JSON: Final = "json"
FORMAT_MARKDOWN: Final = "markdown"
type OutputFormat = Literal["json" | "markdown"]
type JsonData = dict[str, Any]


@dataclass
class InfoArgs:
    common: CommonArgs
    indexes: list[int] | None
    output: OutputFormat


def add_subcommand(subparser: argparse._SubParsersAction[ArgumentParser]) -> None:
    parser = subparser.add_parser(
        SUBCOMMAND_NAME,
        help="Query information about documents from a star-discovery database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.set_defaults(
        run_func=run,
        subcommand_name=SUBCOMMAND_NAME,
        validate_func=validate,
    )
    add_db_arg(parser)
    parser.add_argument(
        "index",
        default=[],
        help="The index(es) of the document(s) to display detailed information "
        "about, with 1 being the first document in the set. If omitted, then "
        "prints a short list of what documents are included in database.",
        nargs="*",
        type=int,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="If provided, has the same effect as including the indexes for "
        "every document in the database.",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=[FORMAT_JSON, FORMAT_MARKDOWN],
        default=FORMAT_MARKDOWN,
        help="The format to use when printing information about selected tables.",
    )
    add_logging_args(parser)


def validate_index_arg(index_arg: list[int], all_flag: bool, db: Database) -> list[int]:
    num_docs = len(db.documents())

    if all_flag:
        if len(index_arg) != 0:
            raise ValueError(
                "Invalid [index]. Cannot provide index value(s) "
                "alongside the --all flag."
            )
        return list(range(1, num_docs + 1))

    for an_index in index_arg:
        if an_index < 1:
            msg = f"Invalid [index]. Indexes must be >= 0 (received {an_index})."
            raise ValueError(msg)
        if an_index > num_docs:
            raise ValueError(
                f"Invalid [index]. Received {an_index} but there are only "
                f"{num_docs} documents in the database.",
            )

    return index_arg


def validate(args: Namespace) -> InfoArgs:
    common_args = common_validate(args, can_create_db=False)

    all_arg = args.all
    index_arg = args.index
    validated_indexes = validate_index_arg(index_arg, all_arg, common_args.database)

    format_arg = args.format

    indexes = None if len(validated_indexes) == 0 else validated_indexes

    return InfoArgs(common_args, indexes, format_arg)


def summary_as_table(summary: RecoverySummary) -> str:
    headers = ["", "source #", "revealed #", "revealed %"]
    html_node_row = [
        "html nodes",
        summary.source.html_node_count(),
        summary.recovered.html_node_count(),
        round(summary.html_node_recovery_pct(), 2),
    ]
    text_node_row = [
        "text nodes",
        summary.source.text_node_count(),
        summary.recovered.text_node_count(),
        round(summary.text_node_recovery_pct(), 2),
    ]
    attrs_row = [
        "html attributes",
        summary.source.attr_name_count(),
        summary.recovered.attr_name_count(),
        round(summary.attr_name_recovery_pct(), 2),
    ]
    attr_values_row = [
        "attr values (non-classes)",
        summary.source.attr_value_count(),
        summary.recovered.attr_value_count(),
        round(summary.attr_value_recovery_pct(), 2),
    ]
    html_classes_row = [
        "html classes",
        summary.source.html_class_count(),
        summary.recovered.html_class_count(),
        round(summary.html_class_recovery_pct(), 2),
    ]
    rows = [html_node_row, text_node_row, attrs_row, attr_values_row, html_classes_row]
    return tabulate(rows, headers)


def summary_as_json(summary: RecoverySummary) -> JsonData:
    return {
        "html nodes": {
            "source": summary.source.html_node_count(),
            "recovered": summary.recovered.html_node_count(),
            "recovered_pct": round(summary.html_node_recovery_pct(), 2),
        },
        "text nodes": {
            "source": summary.source.text_node_count(),
            "recovered": summary.recovered.text_node_count(),
            "recovered_pct": round(summary.text_node_recovery_pct(), 2),
        },
        "html attributes": {
            "source": summary.source.attr_name_count(),
            "recovered": summary.recovered.attr_name_count(),
            "recovered_pct": round(summary.attr_name_recovery_pct(), 2),
        },
        "attr values (non-classes)": {
            "source": summary.source.attr_value_count(),
            "recovered": summary.recovered.attr_value_count(),
            "recovered_pct": round(summary.attr_value_recovery_pct(), 2),
        },
        "html classes": {
            "source": summary.source.html_class_count(),
            "recovered": summary.recovered.html_class_count(),
            "recovered_pct": round(summary.html_class_recovery_pct(), 2),
        },
    }


def run_json_format(args: InfoArgs, indexes: list[int]) -> int:
    db = args.common.database
    documents = db.documents()
    data_output: JsonData = {"database": str(db), "documents": []}

    for an_index in indexes:
        doc = documents[an_index - 1]
        doc_summary = {"document": str(doc), "data": summary_as_json(doc.summary())}
        data_output["documents"].append(doc_summary)

    print(json.dumps(data_output))
    return 0


def run_table_format(args: InfoArgs, indexes: list[int]) -> int:
    db = args.common.database
    documents = db.documents()

    print(str(db))
    print("===")
    print("")

    for an_index in indexes:
        doc = documents[an_index - 1]
        print(str(doc))
        print("---")
        print(summary_as_table(doc.summary()))
        print("")

    return 0


def run(args: InfoArgs) -> int:
    logger = args.common.logger
    db = args.common.database
    documents = db.documents()

    if not args.indexes:
        if len(documents) == 0:
            logger.error("No documents in database.")
            return 1
        for index, doc in enumerate(documents):
            print(f"{index + 1}. {doc}")
        return 0

    if args.output == FORMAT_JSON:
        return run_json_format(args, args.indexes)
    return run_table_format(args, args.indexes)
