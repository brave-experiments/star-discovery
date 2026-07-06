from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup

from star_discovery.database.db import StarDiscoveryDatabase


@dataclass
class ConsumeArgs:
    database_path: Path
    database: StarDiscoveryDatabase
    input: list[Path]


def _create_db_or_throw(db_path: Path) -> StarDiscoveryDatabase:
    if not (db_instance := StarDiscoveryDatabase.create(db_path)):
        raise ValueError(
            f"Invalid path, unable to create a database file at {db_path}."
        )
    return db_instance


def _load_db_or_throw(db_path: Path) -> StarDiscoveryDatabase:
    if not (db_instance := StarDiscoveryDatabase.load(db_path)):
        raise ValueError(
            f"Invalid database path, file at {db_path} is not a valid" "database file."
        )
    return db_instance


def validate_db_path_arg(db_path_arg: Path) -> StarDiscoveryDatabase:
    """Determine what the path for the database should be, given the --database
    argument.

    1. If a file exists at the given path, check if that points to a valid
    existing database file. If so, use that database object, if not, raise
    an exception.
    2. If a directory exists at the given path, then:
        - see if a database file exists in the directory at star-discovery.data.
          if so, check if thats a valid database and use it, or throw
          an exception.
        - if not, see if we can create a star-discovery.data file in the
        directory. If so, create a database there. If not, throw an exception.
    3. If no file and no directory exists at the given path, see if we can
       create a star-discovery database at the path. If so, use that
       database. If not, throw an exception."""

    # Check for case 1 above
    if db_path_arg.is_file():
        return _load_db_or_throw(db_path_arg)

    # Else check for case 2 above
    if db_path_arg.is_dir():
        db_path_in_dir = db_path_arg / StarDiscoveryDatabase.DEFAULT_FILENAME
        if db_path_in_dir.is_file():
            return _load_db_or_throw(db_path_in_dir)
        return _create_db_or_throw(db_path_in_dir)

    # Otherwise, we're at case three above
    return _create_db_or_throw(db_path_arg)


def validate_input_arg(input_paths: list[Path]) -> None:
    for input_path in input_paths:
        try:
            BeautifulSoup(input_path.read_text())
        except Exception as exc:
            err = ValueError(f'Invalid path for --input argument: "{input_path}"')
            raise err from exc


def validate(args: Namespace) -> ConsumeArgs:
    db_path = args.database
    database_instance = validate_db_path_arg(db_path)

    input_paths = args.input
    validate_input_arg(input_paths)

    return ConsumeArgs(db_path, database_instance, input_paths)
