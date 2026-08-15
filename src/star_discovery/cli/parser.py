#!/usr/bin/env python3
from __future__ import annotations

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser
from collections.abc import Callable
from pathlib import Path
from typing import Any

from star_discovery import __version__
import star_discovery.cli.commands.html as html_subcommand
import star_discovery.cli.commands.info as info_subcommand
import star_discovery.cli.commands.read as read_subcommand
from star_discovery.debug import set_debug_mode

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
    html_subcommand.add_subcommand(subparsers)
    info_subcommand.add_subcommand(subparsers)
    read_subcommand.add_subcommand(subparsers)
    return parser


def run() -> int:
    parser = make_parser()
    parsed_args = parser.parse_args()
    subcommand_name = parsed_args.subcommand_name

    validated_args = parsed_args.validate_func(parsed_args)
    set_debug_mode(validated_args.common.debug)

    subcommand_func: Callable[[Any], int] = parsed_args.run_func
    assert callable(subcommand_func)
    return subcommand_func(validated_args)
