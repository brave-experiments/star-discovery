#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from pathlib import Path

from star_discovery import __version__
import star_discovery.cli.commands.read as read_subcommand
import star_discovery.cli.commands.info as info_subcommand

STDOUT_PATH = Path("-")


def make_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="STAR Discovery",
        description="Simulates the STAR-Discovery algorithm on plaintext HTML",
        formatter_class=ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )
    subparsers = parser.add_subparsers()
    subparsers.required = True
    read_subcommand.add_subcommand(subparsers)
    info_subcommand.add_subcommand(subparsers)
    return parser


def run() -> int:
    parser = make_parser()
    parsed_args = parser.parse_args()
    subcommand_name = parsed_args.subcommand_name
    validated_args = parsed_args.validate_func(parsed_args)
    logger = validated_args.common.logger
    logger.info(f"Running subcommand '{subcommand_name}:")
    parsed_args.run_func(validated_args)
    return 0
