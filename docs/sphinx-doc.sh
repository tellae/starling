#!/usr/bin/env bash

sphinx-apidoc -f -T -l -M -o ./docs/src/ ./starling_sim/

sphinx-build -M html ./docs/ ./docs/_build/

printf "\nSi tout c'est bien passé, la doc peut être ouverte en lancant firefox docs/_build/html/overview.html\n"

#firefox ./docs/_build/html/index.html