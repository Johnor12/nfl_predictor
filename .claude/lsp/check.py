# START
# Checks the language server Claude Code starts from this plugin, the way Claude Code starts it.
# - main(): reads the command from .claude-plugin/plugin.json, starts it from outside the repo, opens a
#   scratch file that imports the project's dependencies and has one type error, and passes when pyright
#   reports that error and nothing else (an unresolved import means it isn't reading the uv environment).
# - send(proc, message) / receive(proc): one LSP message over the server's stdin and stdout.
# END
import json
import os
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = Path(__file__).parent / ".claude-plugin" / "plugin.json"
SOURCE = 'import lightgbm\nimport pandas\n\nx: int = "not an int"\n'
ERROR_LINE = 3


def send(proc, message):
    body = json.dumps({"jsonrpc": "2.0", **message}).encode()
    proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    proc.stdin.flush()


def receive(proc):
    length = None
    while line := proc.stdout.readline().strip():
        if line.lower().startswith(b"content-length:"):
            length = int(line.split(b":")[1])
    if length is None:
        sys.exit(f"FAIL: the server exited: {proc.stderr.read().decode().strip()}")
    return json.loads(proc.stdout.read(length))


def main():
    signal.alarm(120)
    server = json.loads(PLUGIN.read_text())["lspServers"]["pyright"]
    args = [arg.replace("${CLAUDE_PROJECT_DIR}", str(ROOT)) for arg in server["args"]]
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    proc = subprocess.Popen([server["command"], *args], cwd=tempfile.gettempdir(), env=env,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    uri = (ROOT / "_lsp_check.py").as_uri()
    send(proc, {"id": 0, "method": "initialize",
                "params": {"processId": os.getpid(), "rootUri": ROOT.as_uri(), "capabilities": {}}})
    while True:
        message = receive(proc)
        if message.get("id") == 0 and "method" not in message:
            send(proc, {"method": "initialized", "params": {}})
            send(proc, {"method": "textDocument/didOpen", "params": {"textDocument": {
                "uri": uri, "languageId": "python", "version": 1, "text": SOURCE}}})
        elif "id" in message and "method" in message:  # a request from the server: answer it emptily
            items = message.get("params", {}).get("items", [])
            send(proc, {"id": message["id"], "result": [None] * len(items) if items else None})
        elif message.get("method") == "textDocument/publishDiagnostics" and message["params"]["uri"] == uri:
            diagnostics = message["params"]["diagnostics"]
            if diagnostics:
                break
    proc.kill()
    for d in diagnostics:
        print(f"line {d['range']['start']['line']}: {d['message'].splitlines()[0]}")
    if [d["range"]["start"]["line"] for d in diagnostics] != [ERROR_LINE]:
        sys.exit("FAIL: expected only the type error on the last line")
    print("ok: pyright runs from the uv environment and reports diagnostics")


if __name__ == "__main__":
    main()
