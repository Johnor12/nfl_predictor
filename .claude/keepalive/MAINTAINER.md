# MAINTAINER

- keepalive.js: everything: the hook commands (`busy`, `idle`), the daemon (`run`), and `status`. Plain Node, no dependencies.
- `../settings.json`: the hooks that call it: `UserPromptSubmit` and `PostToolUse` run `busy`, `Stop` runs `idle`. Each first exits quietly if `node` isn't on PATH, so a machine without it gets no hook errors.

Notes:
- State lives in `/tmp/claude-keepalive/`: `sessions/<session id>` holds `busy` or `idle` (its modification time is the session's last hook event), `daemon.pid`, and `log`.
- The heartbeat is the `NotifyCodespaceOfClientActivity` gRPC call on the host agent's socket (`/workspaces/.codespaces/shared/cs-agent.sock`), the same call the Codespaces VS Code extension and `gh codespace ssh` make. It is written by hand over HTTP/2 to avoid a gRPC dependency. This is not a documented API: if a Codespaces update breaks it, `status` prints `heartbeat: not accepted` and the log fills with `heartbeat not accepted`.
- A command still running after its turn is found by its command line: Claude Code starts every shell command with `source ~/.claude/shell-snapshots/...`. If a Claude Code update changes that, background commands stop being waited for; nothing else breaks.
- The daemon is one process for all sessions. It exits when nothing is working, and the next hook event starts a new one.
- To test by hand: `echo '{"session_id":"test"}' | node keepalive.js busy`, then `status`, then the same with `idle`. The daemon notices within a minute (it keeps going while the testing shell itself is one of Claude's).
- Not proven here: that heartbeats alone hold the codespace past its timeout with no editor connected. The check is to start a long prompt, close the tab for longer than the timeout, and come back.
