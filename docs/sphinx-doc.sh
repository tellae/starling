#!/usr/bin/env bash

sphinx-build -M html ./docs/ ./docs/_build/

printf "\nIf everything went well, the doc may be openned by running \n\nmy_navigator docs/_build/html/index.html\n"