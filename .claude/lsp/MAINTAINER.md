# MAINTAINER

- .claude-plugin/marketplace.json: declares this folder as the `nfl-predictor` marketplace, with one plugin at its root (`"source": "./"`).
- .claude-plugin/plugin.json: the `pyright-uv` plugin. Its one LSP server is the command Claude Code starts for `.py` and `.pyi` files: `python3 langserver.py --stdio`.
- langserver.py: checks that the project environment has a Python for this OS, then runs `uv run --no-sync pyright-langserver` in its place.
- check.py: a smoke test. It starts that command the way Claude Code does and checks the diagnostics for a file that imports the project's dependencies.

## why it's built this way

- Not the official `pyright-lsp` plugin, with `venvPath`/`venv` in pyproject.toml: pyright's config can't follow `UV_PROJECT_ENVIRONMENT`, because it only expands `~`, `${env:HOME}` and `${env:VIRTUAL_ENV}`. Under WSL it would read the Windows `.venv`. Started through `uv run`, pyright takes the interpreter on PATH, which is the project's environment wherever uv keeps it. pyproject.toml has no `[tool.pyright]` venv settings for the same reason.
- `--project ${CLAUDE_PROJECT_DIR}`: Claude Code expands the variable, but doesn't document which working directory it starts the server in.
- `--no-sync`: the server never changes the environment or `uv.lock` while Claude works, and never contacts a package index (see `UV_INDEX` in the root MAINTAINER.md). If the environment is missing pyright, the server fails to start, and `uv sync` fixes it.
- langserver.py, not `uv` as the plugin's command: `uv run` replaces a project environment it can't use, even with `--no-sync`. From WSL with `UV_PROJECT_ENVIRONMENT` unset, it deleted the Windows `.venv` and created an empty Linux one (checked on a copy, 2026-11-16, uv 0.12.21). The check before it costs nothing and turns that into an error. It's started with `python3`, which every machine this runs on has (Linux, WSL, a codespace); it uses only the standard library.
- Under WSL, Claude Code gets `UV_PROJECT_ENVIRONMENT` from `.claude/settings.local.json` (`env`), not from the shell: the variable then reaches the server however Claude Code was started.
- The marketplace path in `.claude/settings.json` is relative (`./.claude/lsp`), and Claude Code resolves it against the repo root. `claude plugin marketplace add --scope project` writes an absolute path instead, which is wrong for a committed file.
- A plugin enabled in project settings from a local-folder marketplace loads in place, with no `claude plugin install` step.
- Baseline: `uv run pyright` reported 201 errors in 45 files on 2026-11-16, mostly values that can be `None` and are used unchecked. Fixing them isn't part of this folder.
