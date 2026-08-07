from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from packaging.version import Version

import star_discovery
from star_discovery.inputs.db import Database, create as create_db, load as load_db
from star_discovery.logging import (
    config as config_logger,
    DEFAULT_LEVEL,
    LEVELS,
)

if TYPE_CHECKING:
    from argparse import Namespace

    from star_discovery.logging import Logger

STDOUT_PATH = Path("-")
type DocIndexes = list[int]


@dataclass
class CommonArgs:
    db_path: Path
    database: Database
    logger: Logger

    def __init__(self, path: Path, db: Database, logger: Logger):
        self.db_path = path
        self.database = db
        self.logger = logger

    def __str__(self) -> str:
        return f"database path: {self.db_path}, logging level: {self.logger.level()}"


def add_indexes_arg(parser: ArgumentParser) -> None:
    parser.add_argument(
        "index",
        default=[],
        help="the index(es) of the document(s) to display detailed information "
        "about, with 1 being the first document in the set. If omitted, then "
        "prints a short list of what documents are included in database.",
        nargs="*",
        type=int,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="if provided, has the same effect as including the indexes "
        "for every document in the database.",
    )


def validate_indexes_arg(args: Namespace, db: Database) -> DocIndexes | None:
    all_flag = args.all
    assert isinstance(all_flag, bool)

    indexes = args.index
    num_docs = len(db.documents())
    if all_flag:
        if len(indexes) != 0:
            raise ValueError(
                "Invalid [index]. Cannot provide index value(s) "
                "alongside the --all flag."
            )
        return list(range(1, num_docs + 1))

    for an_index in indexes:
        if an_index < 1:
            msg = f"Invalid [index]. Indexes must be >= 0 (received {an_index})."
            raise ValueError(msg)
        if an_index > num_docs:
            raise ValueError(
                f"Invalid [index]. Received {an_index} but there are only "
                f"{num_docs} documents in the database.",
            )

    return indexes if len(indexes) > 0 else None


def add_db_arg(parser: ArgumentParser) -> None:
    parser.add_argument(
        "database_path",
        help="the path to an existing star-discovery database or the "
        "path to create a new database at",
        type=Path,
    )


def validate_or_create_db_path_arg(args: Namespace) -> tuple[Path, Database]:
    """Determine what the path for the database should be, given the --database
    argument.

    1. If a file exists at the given path, check if that points to a valid
    existing database file. If so, use that database object, if not, raise
    an exception.
    2. If a directory exists at the given path, then:
        a. see if a database file exists in the directory at star-discovery.db.
           if so, check if thats a valid database and use it, or throw
           an exception.
        b. if not, see if we can create a star-discovery.data file in the
        directory. If so, create a database there. If not, throw an exception.
    3. If no file and no directory exists at the given path, see if we can
       create a star-discovery database at the path. If so, use that
       database. If not, throw an exception."""
    db_path = args.database_path
    threshold = args.threshold

    # Check for case 1 above
    if db_path.is_file():
        return db_path, load_db(db_path)

    # Else check for case 2 above
    if db_path.is_dir():
        db_path_in_dir = db_path / Database.DEFAULT_FILENAME
        # Case 2.a.
        if db_path_in_dir.is_file():
            return db_path_in_dir, load_db(db_path_in_dir)
        # Case 2.b.
        return db_path_in_dir, create_db(db_path_in_dir, threshold)

    # Otherwise, we're at case three above
    return db_path, create_db(db_path, threshold)


def validate_existing_db_path_arg(args: Namespace) -> tuple[Path, Database]:
    """If the given --database argument points to a file, then try
    loading the database file from that path. If it points to a directory,
    try loading a database a file in that directory with the default
    database name. Otherwise, its an invalid argument, so we throw."""
    db_path = args.database_path
    if db_path.is_file():
        return db_path, load_db(db_path)

    if db_path.is_dir():
        db_in_dir_path = db_path / Database.DEFAULT_FILENAME
        return db_in_dir_path, load_db(db_in_dir_path)

    raise ValueError(f'Invalid --database arg. No file or directory at "{db_path}"')


def validate_db_instance(db: Database, threshold: int | None = None) -> None:
    """Checks to make sure that a database instance looks current and like
    something we can work with (meaning that it was created with an expected
    threshold and with a compatible version of this library."""
    db_version = db.version
    lib_version = Version(star_discovery.__version__)

    if db_version.major != lib_version.major:
        raise ValueError(
            f"Major version mismatch. DB version: {db_version}, "
            f"library version: {lib_version}."
        )

    if db_version.minor != lib_version.minor:
        raise ValueError(
            f"Minor version mismatch. DB version: {db_version}, "
            f"library version: {lib_version}."
        )

    if threshold and db.threshold != threshold:
        raise ValueError(
            f"Threshold mismatch. DB was created with threshold {db.threshold}, "
            f"but expect threshold of {threshold}."
        )


def add_logging_args(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--log-path",
        default=STDOUT_PATH,
        help="Path to write logging information to. Defaults to '-', "
        "or that logs will be written stdout.",
        type=Path,
    )
    parser.add_argument(
        "-l",
        "--log-level",
        choices=LEVELS,
        default=DEFAULT_LEVEL,
        help="Specify how how much information to log, with 'debug' being "
        "the most information logged, and 'quiet' being the least (i.e., "
        "no information logged). Note that errors are always logged, "
        "irrespective of this value.",
    )


def validate_logging_arg(args: Namespace) -> Logger:
    log_level = args.log_level
    return config_logger(log_level)


def add_common_args(parser: ArgumentParser) -> None:
    """Add the database and logging arguments that every command requires."""
    add_db_arg(parser)
    add_logging_args(parser)


def validate_common_args(
    args: Namespace, can_create_db: bool = True, threshold: int | None = None
) -> CommonArgs:
    if can_create_db:
        db_path, db_instance = validate_or_create_db_path_arg(args)
    else:
        db_path, db_instance = validate_existing_db_path_arg(args)

    validate_db_instance(db_instance, threshold)

    logger = validate_logging_arg(args)
    return CommonArgs(db_path, db_instance, logger)
