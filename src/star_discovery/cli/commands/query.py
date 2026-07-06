from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path

from star_discovery.database.db import StarDiscoveryDatabase


@dataclass
class QueryArgs:
    database_path: Path
    database: StarDiscoveryDatabase | None


def validate_db_path_arg(db_path_arg: Path) -> StarDiscoveryDatabase:
    """If the given --database argument points to a file, then try
    loading the database file from that path. If it points to a directory,
    try loading a database a file in that directory with the default
    database name. Otherwise, its an invalid argument, so we throw."""
    if db_path_arg.is_file():
        if not (db_instance := StarDiscoveryDatabase.load(db_path_arg)):
            raise ValueError(
                f'Invalid --database arg. "{db_path_arg}" is not a valid '
                "database file."
            )
        return db_instance

    if db_path_arg.is_dir():
        db_in_dir_path = db_path_arg / StarDiscoveryDatabase.DEFAULT_FILENAME
        if not (db_instance := StarDiscoveryDatabase.load(db_in_dir_path)):
            raise ValueError(
                "Invalid --database arg. Could not load a database from "
                f'"{db_in_dir_path}".'
            )
        return db_instance

    raise ValueError(f'Invalid --database arg. No file or directory at "{db_path_arg}"')


def validate(args: Namespace) -> QueryArgs:
    return QueryArgs(args.database, None)
