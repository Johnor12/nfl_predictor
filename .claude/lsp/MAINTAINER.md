# MAINTAINER

- .claude-plugin/marketplace.json: declares this folder as the `nfl-predictor` marketplace, with one plugin at its root (`"source": "./"`).
- .claude-plugin/plugin.json: the `pyright-uv` plugin. Its one LSP server is the command Claude Code starts for `.py` and `.pyi` files.
- check.py: a smoke test. It starts that command the way Claude Code does and checks the diagnostics for a file that imports the project's dependencies.

## why it's built this way

- Not the official `pyright-lsp` plugin, with `venvPath`/`venv` in pyproject.toml: pyright's config can't follow `UV_PROJECT_ENVIRONMENT`, because it only expands `~`, `${env:HOME}` and `${env:VIRTUAL_ENV}`. Under WSL it would read the Windows `.venv`. Started through `uv run`, pyright takes the interpreter on PATH, which is the project's environment wherever uv keeps it. pyproject.toml has no `[tool.pyright]` venv settings for the same reason.
- `--project ${CLAUDE_PROJECT_DIR}`: Claude Code expands the variable, but doesn't document which working directory it starts the server in.
- `--no-sync`: the server never changes the environment or `uv.lock` while Claude works, and never contacts a package index (see `UV_INDEX` in the root MAINTAINER.md). If the environment is missing pyright, the server fails to start, and `uv sync` fixes it.
- The marketplace path in `.claude/settings.json` is relative (`./.claude/lsp`), and Claude Code resolves it against the repo root. `claude plugin marketplace add --scope project` writes an absolute path instead, which is wrong for a committed file.
- A plugin enabled in project settings from a local-folder marketplace loads in place, with no `claude plugin install` step.
- Baseline: `uv run pyright` reported 201 errors in 45 files on 2026-11-16, mostly values that can be `None` and are used unchecked. Fixing them isn't part of this folder.
