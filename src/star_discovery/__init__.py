from pathlib import Path
import tomllib


def read_version() -> str:
    script_path = Path(__file__).parent.absolute()
    with open(script_path / "../../pyproject.toml", "rb") as handle:
        data = tomllib.load(handle)
        version = data["project"]["version"]
        assert isinstance(version, str)
        return version


__author__ = "Peter Snyder (pes@brave.com)"
__version__ = read_version()
