from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import TYPE_CHECKING

from star_discovery.cli.commands.common import (
    add_common_args,
    add_indexes_arg,
    CommonArgs,
    validate_indexes_arg,
    validate_common_args,
)

if TYPE_CHECKING:
    from star_discovery.logging import Logger
    from star_discovery.inputs.db import Database

SUBCOMMAND_NAME = "html"


@dataclass
class HTMLArgs:
    common: CommonArgs
    indexes: list[int] | None
    inc_hidden: bool


def add_subcommand(subparser: argparse._SubParsersAction[ArgumentParser]) -> None:
    subcommand = subparser.add_parser(
        SUBCOMMAND_NAME,
        help="generate HTML based on the recovered portion of each input document",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subcommand.set_defaults(
        run_func=run,
        subcommand_name=SUBCOMMAND_NAME,
        validate_func=validate,
    )
    add_common_args(subcommand)
    add_indexes_arg(subcommand)
    subcommand.add_argument(
        "--hidden",
        action="store_true",
        help="include portion of the HTML document that were not recovered "
        "(i.e., they didn't match the threshold). These not-recovered "
        "elements are included in a way designed to not be rendered when "
        "viewed, such as namespaced html-attributes or comments.",
    )


def validate(args: Namespace) -> HTMLArgs:
    common_args = validate_common_args(args, can_create_db=False)
    db = common_args.database

    indexes = validate_indexes_arg(args, db)
    return HTMLArgs(common_args, indexes, args.hidden)


def run(args: HTMLArgs) -> int:
    db = args.common.database
    logger = args.common.logger
    logger.debug(f"Running {SUBCOMMAND_NAME} with database: {db}:")

    documents = db.documents()
    if not args.indexes:
        if len(documents) == 0:
            logger.error("No documents in database.")
            return 1
        for index, doc in enumerate(documents):
            print(f"{index + 1}. {doc}")
        logger.error("Must select at least one document to render as HTML.")
        return 1

    for an_index in args.indexes:
        doc = documents[an_index - 1]
        print(doc.recovered_html(args.inc_hidden).prettify())
    return 0
