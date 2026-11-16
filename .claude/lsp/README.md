# lsp

Gives Claude Code a Python language server for this repo: pyright, run from the repo's uv environment. With it, Claude sees pyright's errors after each edit of a `.py` file, and can use go-to-definition, find-references and hover.

## how it's used

Nothing to run: `.claude/settings.json` declares this folder as a plugin marketplace (`nfl-predictor`) and turns on its one plugin, `pyright-uv`. It also turns off the official `pyright-lsp` plugin for this repo, because that one runs whatever pyright and Python are on PATH.

The server is started as `uv run --no-sync pyright-langserver`, so it reads the environment that uv uses on each machine: `.venv` on Linux and in a codespace, and `$UV_PROJECT_ENVIRONMENT` under WSL. pyright and pandas-stubs are dev dependencies, so `uv sync` installs them and every machine runs the same pyright.

## on a new machine

- Run `uv sync`. pyright runs on node: it uses the one on PATH, or downloads one on first use.
- Trust the folder when Claude Code asks. The plugin loads at the next session start, and `/plugin` lists it.

## commands

- `python3 .claude/lsp/check.py`: starts the server the way Claude Code does and checks that it resolves the project's imports (about a second).
- `uv run pyright [paths]`: the same checks from the command line (about 15 seconds for the whole repo).
