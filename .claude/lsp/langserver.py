# START
# The command Claude Code starts for this plugin's language server (.claude-plugin/plugin.json).
# - main(): finds the project's uv environment where uv looks for it (UV_PROJECT_ENVIRONMENT, else .venv) and
#   runs pyright-langserver in it with `uv run --no-sync`. It refuses when that folder has no Python for this
#   OS (the Windows .venv seen from WSL, say): uv would delete it and create an empty one, even with --no-sync.
# END
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main():
    env = ROOT / os.environ.get("UV_PROJECT_ENVIRONMENT", ".venv")
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.exists():
        sys.exit(f"pyright-uv: {env} has no {python.relative_to(env)}, and uv would replace it with an empty "
                 "environment. Run `uv sync`; under WSL, set UV_PROJECT_ENVIRONMENT first (.claude/lsp/README.md).")
    os.execvp("uv", ["uv", "run", "--project", str(ROOT), "--no-sync", "pyright-langserver", *sys.argv[1:]])


if __name__ == "__main__":
    main()
