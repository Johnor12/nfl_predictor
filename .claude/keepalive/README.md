# keepalive

Keeps the GitHub codespace awake while Claude Code is working, so a long prompt isn't cut off by the codespace's idle timeout. When the work is done it stops, and the codespace shuts down after its usual idle timeout (30 minutes by default), not straight away.

A codespace only counts activity that a connected editor reports (typing, terminal output). With the browser tab closed or the laptop asleep nothing is reported, and the codespace stops after the timeout however busy Claude is.

## how it's used

Nothing to run: `.claude/settings.json` hooks it into Claude Code.

- A prompt is submitted, or a tool call finishes: the session is marked busy, and a background daemon starts sending the codespace a heartbeat every minute.
- Claude finishes its turn: the session is marked idle. The daemon stops at its next heartbeat, unless a shell command Claude started is still running (an evaluation in the background, say); then it waits for that.

Outside a codespace it does nothing, and where `node` isn't installed (WSL, say) the hooks skip it.

## commands

- `node .claude/keepalive/keepalive.js status`: the sessions it knows, whether the daemon is running, and whether the codespace accepts a heartbeat.
- `/tmp/claude-keepalive/log`: when it started and stopped keeping the codespace awake.

## limits

- A turn that is interrupted (Esc) or killed never reports that it finished. It is given up on 60 minutes after its last tool call.
- A command that outlives its turn is waited for up to 6 hours. A server left running in the background counts, so stop it when it's no longer needed.
- VS Code closes a terminal whose editor has been disconnected for 3 hours, and Claude Code with it. To outlast that, run `claude` inside `tmux`.
