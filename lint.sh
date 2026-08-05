#!/bin/bash
set -euo pipefail
IFS=$'\n\t'


black --diff --color src/ || echo "";
pylint --rcfile ./pylintrc src/ || echo "";
mypy --config-file mypy.ini --strict src/ || echo "";
