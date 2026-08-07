from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import json
from typing import Any, Literal, Final, TYPE_CHECKING

from tabulate import tabulate

from star_discovery.cli.commands.common import (
    add_common_args,
    add_indexes_arg,
    CommonArgs,
    validate_common_args,
    validate_indexes_arg,
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
        help="query information about documents from a star-discovery database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.set_defaults(
        run_func=run,
        subcommand_name=SUBCOMMAND_NAME,
        validate_func=validate,
    )
    add_common_args(parser)
    add_indexes_arg(parser)
    parser.add_argument(
        "--format",
        "-f",
        choices=[FORMAT_JSON, FORMAT_MARKDOWN],
        default=FORMAT_MARKDOWN,
        help="the format to use when printing information about selected tables.",
    )


def validate(args: Namespace) -> InfoArgs:
    common_args = validate_common_args(args, can_create_db=False)
    db = common_args.database

    indexes = validate_indexes_arg(args, db)
    format_arg = args.format
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
    logger = args.common.logger
    documents = db.documents()
    data_output: JsonData = {"database": str(db), "documents": []}

    for an_index in indexes:
        doc = documents[an_index - 1]
        summary = doc.summary(logger)
        summary_data = {"document": str(doc), "data": summary_as_json(summary)}
        data_output["documents"].append(summary_data)

    print(json.dumps(data_output))
    return 0


def run_table_format(args: InfoArgs, indexes: list[int]) -> int:
    db = args.common.database
    logger = args.common.logger
    documents = db.documents()

    print(str(db))
    print("===")
    print("")

    for an_index in indexes:
        doc = documents[an_index - 1]
        summary = doc.summary(logger)
        print(str(doc))
        print("---")
        print(summary_as_table(summary))
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
        print(str(db))
        for index, doc in enumerate(documents):
            print(f"{index + 1}. {doc}")
        return 0

    if args.output == FORMAT_JSON:
        return run_json_format(args, args.indexes)
    return run_table_format(args, args.indexes)
