#!/usr/bin/env bash

black --diff --color src/
pylint --rcfile ./pylintrc src/
mypy --config-file mypy.ini --strict src/
