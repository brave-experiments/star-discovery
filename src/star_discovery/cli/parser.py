#!/usr/bin/env python3

import argparse
from pathlib import Path

from star_discovery import __version__
import star_discovery.cli.commands.consume as consume_cmd
import star_discovery.cli.commands.query as query_cmd


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="STAR Discovery",
        description="Simulates the STAR-Discovery algorithm on plaintext HTML",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-v", "--version", action="version", version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(help="subcommands")

    consume_parser = subparsers.add_parser(
        "consume",
        help="Read input files into a star-discovery database.",
    )
    consume_parser.add_argument(
        "-i",
        "--input",
        help="Paths to input files (HTML documents)",
        nargs="*",
        required=True,
        type=Path,
    )
    consume_parser.add_argument(
        "-d",
        "--database",
        help="Either the path to an existing star-discovery database, or the "
        "path to create a new database.",
        required=True,
        type=Path,
    )
    consume_parser.set_defaults(validate=consume_cmd.validate)

    query_parser = subparsers.add_parser(
        "query",
        help="Query an existing star-discovery database.",
    )
    query_parser.add_argument(
        "-d",
        "--database",
        help="Path to an existing star-discovery database.",
        required=True,
        type=Path,
    )
    query_parser.set_defaults(validate=query_cmd.validate)

    return parser


def run() -> int:
    parser = make_parser()
    args = parser.parse_args()
    valid_args = args.validate(args)
    print(valid_args)
    return 0
