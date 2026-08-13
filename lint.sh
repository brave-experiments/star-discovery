#!/bin/bash
set -euo pipefail
IFS=$'\n\t'


black --diff --color src/ tests/ || echo "";
pylint --rcfile ./pylintrc src/ tests/ || echo "";
mypy --config-file pyproject.toml src/ tests/ || echo "";
