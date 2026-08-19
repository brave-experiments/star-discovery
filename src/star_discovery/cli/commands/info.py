from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
import json
from typing import TYPE_CHECKING

from tabulate import tabulate

from star_discovery.cli.commands.common import (
    add_common_args,
    add_indexes_arg,
    CommonArgs,
    validate_common_args,
    validate_indexes_arg,
)
from star_discovery.summaries import NodeType, NodeTypeCount

if TYPE_CHECKING:
    from typing import Any, Literal, Final

    from star_discovery.inputs.db import Database
    from star_discovery.inputs.document import Document, RecoverySummary
    from star_discovery.summaries import DepthSummary

SUBCOMMAND_NAME = "info"
FORMAT_JSON: Final = "json"
FORMAT_MARKDOWN: Final = "markdown"
type OutputFormat = Literal["json" | "markdown"]
type JsonData = dict[str, Any]

JSON_SOURCE_KEY: Final = "source"
JSON_RECOVERED_KEY: Final = "recovered"
JSON_RECOVERED_PCT_KEY: Final = "recovered_pct"


@dataclass
class InfoArgs:
    common: CommonArgs
    depth: bool
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
        "--depth",
        "-d",
        action="store_true",
        help="present information about node recovery by depth (i.e., the "
        "number of nodes of depth 1, 2, 3, etc. recovered.",
    )
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
    depth_arg = args.depth
    return InfoArgs(common_args, depth_arg, indexes, format_arg)


def _depth_table_cell(
    node_type: NodeType | Literal["total"],
    source: NodeTypeCount,
    recovered: NodeTypeCount,
) -> str:
    if node_type == "total":
        source_amt = source.total()
        recovered_amt = recovered.total()
    else:
        source_amt = source[node_type]
        recovered_amt = recovered[node_type]

    if source_amt == 0 and recovered_amt == 0:
        return "-"

    if source_amt > 0:
        recovered_pct_value = recovered_amt / float(source_amt)
        recovered_pct_cell = f"{recovered_pct_value:.2}"
    else:
        recovered_pct_cell = "-"
    return f"{recovered_amt} / {source_amt} ({recovered_pct_cell})"




def depth_info_as_table(doc: Document) -> str:
    source_summary = doc.source_depths_summary()
    recovered_summary = doc.recovered_depths_summary()
    num_recovered_rows = len(recovered_summary)

    header_row = [
        "depth",
        NodeType.HTML.value,
        NodeType.TEXT.value,
        NodeType.NAME.value,
        NodeType.VALUE.value,
        "total",
    ]

    source_totals_row = NodeTypeCount()
    recovered_totals_row = NodeTypeCount()
    body_rows = []

    for depth_index, source_row in enumerate(source_summary):
        if depth_index >= num_recovered_rows:
            recovered_row = NodeTypeCount()
        else:
            recovered_row = recovered_summary[depth_index]
        source_totals_row += source_row
        recovered_totals_row += recovered_row

        row = [
            str(depth_index),
            _depth_table_cell(NodeType.HTML, source_row, recovered_row),
            _depth_table_cell(NodeType.TEXT, source_row, recovered_row),
            _depth_table_cell(NodeType.NAME, source_row, recovered_row),
            _depth_table_cell(NodeType.VALUE, source_row, recovered_row),
            _depth_table_cell("total", source_row, recovered_row),
        ]
        body_rows.append(row)

    totals_row = [
        "total",
        _depth_table_cell(NodeType.HTML, source_totals_row, recovered_totals_row),
        _depth_table_cell(NodeType.TEXT, source_totals_row, recovered_totals_row),
        _depth_table_cell(NodeType.NAME, source_totals_row, recovered_totals_row),
        _depth_table_cell(NodeType.VALUE, source_totals_row, recovered_totals_row),
        _depth_table_cell("total", source_totals_row, recovered_totals_row),
    ]
    body_rows.append(totals_row)
    return tabulate(body_rows, headers=header_row, colglobalalign="right")


def _depth_json_cell(
    node_type: NodeType, source: NodeTypeCount, recovered: NodeTypeCount
) -> JsonData:
    source_amt = source[node_type]
    recovered_amt = recovered[node_type]
    recovered_pct = recovered_amt / float(source_amt) if source_amt else "-"
    return {
        JSON_SOURCE_KEY: source_amt,
        JSON_RECOVERED_KEY: recovered_amt,
        JSON_RECOVERED_PCT_KEY: recovered_pct,
    }


def depth_info_as_json(doc: Document) -> JsonData:
    source_summary = doc.source_depths_summary()
    recovered_summary = doc.recovered_depths_summary()
    num_recovered_rows = len(recovered_summary)

    source_totals = NodeTypeCount()
    recovered_totals = NodeTypeCount()

    depths_rows: dict[int, JsonData] = {}
    for depth_index in range(num_recovered_rows):
        source_row = source_summary[depth_index]
        if depth_index >= num_recovered_rows:
            recovered_row = NodeTypeCount()
        else:
            recovered_row = recovered_summary[depth_index]

        source_totals += source_row
        recovered_totals += recovered_row

        depths_rows[depth_index] = {
            NodeType.HTML.value: _depth_json_cell(
                NodeType.HTML, source_row, recovered_row
            ),
            NodeType.TEXT.value: _depth_json_cell(
                NodeType.TEXT, source_row, recovered_row
            ),
            NodeType.NAME.value: _depth_json_cell(
                NodeType.NAME, source_row, recovered_row
            ),
            NodeType.VALUE.value: _depth_json_cell(
                NodeType.VALUE, source_row, recovered_row
            ),
        }

    total_data = {
        NodeType.HTML.value: _depth_json_cell(
            NodeType.HTML, source_totals, recovered_totals
        ),
        NodeType.TEXT.value: _depth_json_cell(
            NodeType.TEXT, source_totals, recovered_totals
        ),
        NodeType.NAME.value: _depth_json_cell(
            NodeType.NAME, source_totals, recovered_totals
        ),
        NodeType.VALUE.value: _depth_json_cell(
            NodeType.VALUE, source_totals, recovered_totals
        ),
    }
    return {
        "depths": depths_rows,
        "total": total_data,
    }


def summary_as_table(summary: RecoverySummary) -> str:
    header_row = ["type", "source #", "revealed #", "revealed %"]
    body_rows = [
        (
            NodeType.HTML.value,
            summary.source.html_node_count(),
            summary.recovered.html_node_count(),
            summary.html_node_recovery_pct(),
        ),
        (
            NodeType.TEXT.value,
            summary.source.text_node_count(),
            summary.recovered.text_node_count(),
            summary.text_node_recovery_pct(),
        ),
        (
            NodeType.NAME.value,
            summary.source.attr_name_count(),
            summary.recovered.attr_name_count(),
            summary.attr_name_recovery_pct(),
        ),
        (
            NodeType.VALUE.value,
            summary.source.attr_value_count(),
            summary.recovered.attr_value_count(),
            summary.attr_value_recovery_pct(),
        ),
    ]

    source_total = sum((x[1] for x in body_rows))
    recovery_total = sum((x[2] for x in body_rows))
    totals_row = (
        "total",
        source_total,
        recovery_total,
        recovery_total / float(source_total),
    )
    body_rows.append(totals_row)

    return tabulate(body_rows, headers=header_row)


def summary_as_json(summary: RecoverySummary) -> JsonData:

    data: JsonData = {
        NodeType.HTML.value: {
            JSON_SOURCE_KEY: summary.source.html_node_count(),
            JSON_RECOVERED_KEY: summary.recovered.html_node_count(),
            JSON_RECOVERED_PCT_KEY: round(summary.html_node_recovery_pct(), 2),
        },
        NodeType.TEXT.value: {
            JSON_SOURCE_KEY: summary.source.text_node_count(),
            JSON_RECOVERED_KEY: summary.recovered.text_node_count(),
            JSON_RECOVERED_PCT_KEY: round(summary.text_node_recovery_pct(), 2),
        },
        NodeType.NAME.value: {
            JSON_SOURCE_KEY: summary.source.attr_name_count(),
            JSON_RECOVERED_KEY: summary.recovered.attr_name_count(),
            JSON_RECOVERED_PCT_KEY: round(summary.attr_name_recovery_pct(), 2),
        },
        NodeType.VALUE.value: {
            JSON_SOURCE_KEY: summary.source.attr_value_count(),
            JSON_RECOVERED_KEY: summary.recovered.attr_value_count(),
            JSON_RECOVERED_PCT_KEY: round(summary.attr_value_recovery_pct(), 2),
        },
    }

    source_total = sum(x[JSON_SOURCE_KEY] for x in data.values())
    recovered_total = sum(x[JSON_RECOVERED_KEY] for x in data.values())
    recovered_rate_total = recovered_total / float(source_total)

    data["total"] = {
        JSON_SOURCE_KEY: source_total,
        JSON_RECOVERED_KEY: recovered_total,
        JSON_RECOVERED_PCT_KEY: recovered_rate_total,
    }
    return data


def run_json_format(args: InfoArgs, indexes: list[int]) -> int:
    db = args.common.database
    logger = args.common.logger
    show_depths_info = args.depth

    documents = db.documents()
    data_output: JsonData = {"database": str(db), "documents": []}

    for an_index in indexes:
        doc = documents[an_index - 1]
        if show_depths_info:
            depth_data = depth_info_as_json(doc)
            data_output["documents"].append(depth_data)
        else:
            summary = doc.summary(logger)
            summary_data = {"document": str(doc), "data": summary_as_json(summary)}
            data_output["documents"].append(summary_data)

    print(json.dumps(data_output))
    return 0


def run_table_format(args: InfoArgs, indexes: list[int]) -> int:
    db = args.common.database
    logger = args.common.logger
    show_depths_info = args.depth

    documents = db.documents()
    print(str(db))
    print("===")
    print("")

    for an_index in indexes:
        doc = documents[an_index - 1]
        print(str(doc))
        print("---")
        if show_depths_info:
            print(depth_info_as_table(doc))
        else:
            summary = doc.summary(logger)
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
