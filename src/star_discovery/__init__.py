from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass
class ProjectData:
    name: str
    version: str


def read_pyproject() -> ProjectData:
    script_path = Path(__file__).parent.absolute()
    with open(script_path / "../../pyproject.toml", "rb") as handle:
        data = tomllib.load(handle)
        version = data["project"]["version"]
        assert isinstance(version, str)
        name = data["project"]["name"]
        assert isinstance(name, str)
        return ProjectData(name, version)


PROJECT_DATA = read_pyproject()

__author__ = "Peter Snyder (pes@brave.com)"
__version__ = PROJECT_DATA.version
NAME = PROJECT_DATA.name
