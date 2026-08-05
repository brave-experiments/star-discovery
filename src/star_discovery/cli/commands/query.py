from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass

from star_discovery.cli.commands.common import (
    CommonArgs,
    add_db_arg,
    add_logging_args,
    validate as common_validate,
)

SUBCOMMAND_NAME = "query"


@dataclass
class QueryArgs(CommonArgs):

    def __init__(self, common_args: CommonArgs):
        super().__init__(common_args.db_path, common_args.database, common_args.logger)


def add_subcommand(subparser: argparse._SubParsersAction[ArgumentParser]) -> None:
    query_parser = subparser.add_parser(
        SUBCOMMAND_NAME,
        help="Query information from a star-discovery database.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    query_parser.set_defaults(
        run_func=run,
        subcommand_name=SUBCOMMAND_NAME,
        validate_func=validate,
    )
    add_db_arg(query_parser)
    add_logging_args(query_parser)


def validate(args: Namespace) -> QueryArgs:
    common_args = common_validate(args, can_create_db=False)
    return QueryArgs(common_args)


def run(args: QueryArgs) -> None:
    pass
