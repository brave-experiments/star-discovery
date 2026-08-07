from __future__ import annotations

import argparse
from argparse import ArgumentParser, Namespace
from dataclasses import dataclass
from typing import TYPE_CHECKING
from pathlib import Path

from bs4 import BeautifulSoup

from star_discovery.cli.commands.common import (
    add_common_args,
    CommonArgs,
    validate_common_args,
)

if TYPE_CHECKING:
    from star_discovery.logging import Logger
    from star_discovery.inputs.db import Database

THRESHOLD_MINIMUM = 2
SUBCOMMAND_NAME = "read"


@dataclass
class InputFile:
    path: Path
    data: BeautifulSoup


@dataclass
class ConsumeArgs:
    common: CommonArgs
    inputs: list[InputFile]
    threshold: int


def add_subcommand(subparser: argparse._SubParsersAction[ArgumentParser]) -> None:
    consume_parser = subparser.add_parser(
        SUBCOMMAND_NAME,
        help="read input files into a star-discovery database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    consume_parser.set_defaults(
        run_func=run,
        subcommand_name=SUBCOMMAND_NAME,
        validate_func=validate,
    )
    add_common_args(consume_parser)
    consume_parser.add_argument(
        "input",
        help="paths to input files (HTML documents)",
        nargs="+",
        type=Path,
    )
    consume_parser.add_argument(
        "-t",
        "--threshold",
        default=2,
        help="the threshold to use when simulating key-recovery (i.e., the K "
        "in the STAR recovery algorithm)",
        type=int,
    )


def validate_input_arg(args: Namespace) -> list[InputFile]:
    parsed_inputs: list[InputFile] = []
    for input_path in args.input:
        try:
            html_text = input_path.read_text()
        except FileNotFoundError:
            # pylint: disable-next=raise-missing-from
            raise ValueError(f'Invalid path for --input argument: "{input_path}"')

        try:
            bs = BeautifulSoup(html_text, features="html.parser")
            parsed_inputs.append(InputFile(input_path, bs))
        except ValueError:
            # pylint: disable-next=raise-missing-from
            raise ValueError(f'Invalid path for --input argument: "{input_path}"')
    return parsed_inputs


def validate_threshold_arg(args: Namespace) -> int:
    assert isinstance(args.threshold, int)
    if args.threshold < THRESHOLD_MINIMUM:
        raise ValueError(
            f"Invalid value for --threshold. Value must be at least {THRESHOLD_MINIMUM}"
        )
    return args.threshold


def validate(args: Namespace) -> ConsumeArgs:
    threshold = validate_threshold_arg(args)
    common_args = validate_common_args(args, can_create_db=True, threshold=threshold)
    input_data = validate_input_arg(args)
    return ConsumeArgs(common_args, input_data, threshold)


def run(args: ConsumeArgs) -> int:
    db = args.common.database
    logger = args.common.logger
    logger.debug(f"Running {SUBCOMMAND_NAME} with database: {db}:")

    for input_file in args.inputs:
        input_path = input_file.path.absolute()
        input_html = input_file.data
        db.add_document(input_html, input_path, logger)

    for index, doc in enumerate(db.documents()):
        logger.info(f"{index + 1}. {doc}")
    logger.info(f"Completed database: {db}.")

    db_path = args.common.db_path
    db_path.unlink()
    db.save(db_path, logger)
    return 0
