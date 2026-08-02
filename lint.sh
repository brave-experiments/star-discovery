#!/bin/bash
set -euo pipefail
IFS=$'\n\t'


black --diff --color src/
pylint --rcfile ./pylintrc src/
mypy --config-file mypy.ini --strict src/
