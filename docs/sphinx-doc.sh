#!/usr/bin/env bash

sphinx-apidoc -f -T -l -M -o ./docs/src/ ./starling_sim/

sphinx-build -M html ./docs/ ./docs/_build/

printf "\nIf everything went well, the doc may be openned by running docs/_build/html/overview.html\n"

#firefox ./docs/_build/html/index.html