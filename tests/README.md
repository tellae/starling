# Starling tests

Run tests from the root of the project using pytest

```bash
pytest
```

More information on the tests can be obtained with the verbose option

```bash
pytest -v
```

Tests coverage can be obtained with the plugin pytest-cov with option

```bash
python3 -m pytest --cov=starling_sim tests/ --cov-report html
```
