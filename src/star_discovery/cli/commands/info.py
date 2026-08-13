from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import json
from typing import Any, Literal, Final, TYPE_CHECKING

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
        help="query information about documents from a star-discovery database",
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
    first_col_width = 20
    type MarkupRow = tuple[str, str, str]
    markup_rows: list[MarkupRow] = [
        (
            "source #",
            "revealed #",
            "revealed %",
        ),
        (
            "    ----",
            "      ----",
            "      ----",
        ),
    ]

    def _format_markup(row: MarkupRow) -> str:
        output: str = " " * first_col_width
        output += "  ".join(row)
        return output

    type DataRow = tuple[str, int, int, float]
    body_rows: list[DataRow] = [
        (
            "html nodes",
            summary.source.html_node_count(),
            summary.recovered.html_node_count(),
            summary.html_node_recovery_pct(),
        ),
        (
            "text nodes",
            summary.source.text_node_count(),
            summary.recovered.text_node_count(),
            summary.text_node_recovery_pct(),
        ),
        (
            "html attributes",
            summary.source.attr_name_count(),
            summary.recovered.attr_name_count(),
            summary.attr_name_recovery_pct(),
        ),
        (
            "other attrs values",
            summary.source.attr_value_count(),
            summary.recovered.attr_value_count(),
            summary.attr_value_recovery_pct(),
        ),
    ]

    def _format_data(row: DataRow) -> str:
        column, source_num, recover_num, pct = row
        return f"{column:<18}  {source_num:>8}    {recover_num:>8}    {pct:>8.2f}"

    table_output = "\n".join((_format_markup(x) for x in markup_rows))
    table_output += "\n" + "\n".join((_format_data(x) for x in body_rows))

    footer_row: MarkupRow = (
        "    ====",
        "      ====",
        "      ====",
    )
    source_total = sum((x[1] for x in body_rows))
    recovery_total = sum((x[2] for x in body_rows))
    total_row: DataRow = (
        "total",
        source_total,
        recovery_total,
        recovery_total / float(source_total),
    )

    table_output += "\n" + _format_markup(footer_row)
    table_output += "\n" + _format_data(total_row)
    return table_output


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
