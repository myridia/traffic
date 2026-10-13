# Project: traffic

## Overview
Python CLI that ranks a GitHub owner's repositories by **clones** (last 14 days,
via the traffic API) or by **stars** (public). Output goes to stdout and,
optionally, to a CSV.

## Stack
- Python >= 3.13, Poetry (package-mode off)
- `requests` only dependency
- Plain script, no tests, no Docker

## Structure
- `main.py` - the CLI (argument parsing, repo listing, clones/stars ranking)
- `clones.csv` - sample output: `name,value,extra` (value = clone count)
- `pyproject.toml` - Poetry config
- `traffic.svg` - README logo
- No `ask.sh`

## Run
```bash
poetry install
export GITHUB_TOKEN=ghp_xxxxxxxx
poetry run python main.py --owner myridia --by clones --csv clones.csv
poetry run python main.py --owner myridia --by stars --csv stars.csv
```

- `--by clones` needs a token with repo access to those repos (the traffic
  endpoint is private); missing permission prints `Skipping <repo>: 403 ...`.
- `--by stars` is public and works without a token.
- `--sleep` (default 0.4s) paces the per-repo traffic calls.
