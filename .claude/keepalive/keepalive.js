// START
// Keeps this GitHub codespace awake while Claude Code is working. Claude Code's hooks run it
// (.claude/settings.json); it does nothing outside a codespace.
// - mark(state): the `busy` and `idle` commands. Records the hook's session as mid-turn or finished, and
//   starts the daemon if it isn't running.
// - working() -> bool: whether anything still needs the codespace: a session mid-turn, or a shell command
//   Claude started that is still running after its turn ended.
// - heartbeat() -> Promise<bool>: tells the codespace's host agent there was activity, which restarts its
//   idle timer. True if the agent accepted it.
// - run(): the `run` command, the daemon: a heartbeat a minute while working(), then it exits and the
//   codespace's own idle timeout counts down as usual.
// - status(): the `status` command. Prints the sessions, the daemon, and the result of one heartbeat.
// END
const fs = require('fs');
const http2 = require('http2');
const net = require('net');
const path = require('path');
const { spawn, spawnSync } = require('child_process');

const DIR = process.env.KEEPALIVE_DIR || '/tmp/claude-keepalive'; // the variable is for tests
const SESSIONS = path.join(DIR, 'sessions');
const PIDFILE = path.join(DIR, 'daemon.pid');
const LOG = path.join(DIR, 'log');

// The host agent's gRPC endpoint; the Codespaces extension and `gh codespace ssh` report activity here too.
const SOCKET = '/workspaces/.codespaces/shared/cs-agent.sock';
const RPC = '/Codespaces.Grpc.CodespaceHostService.v1.CodespaceHost/NotifyCodespaceOfClientActivity';

const MINUTE = 60_000;
const QUIET_TURN = 60 * MINUTE; // a turn with no tool call for this long was interrupted or killed
const BACKGROUND = 6 * 60 * MINUTE; // the longest a command may outlive its turn and still be waited for

function log(text) {
  fs.appendFileSync(LOG, `${new Date().toISOString()} ${text}\n`);
}

function age(file) {
  return Date.now() - fs.statSync(file).mtimeMs;
}

function daemonRunning() {
  try {
    const pid = fs.readFileSync(PIDFILE, 'utf8');
    return fs.readFileSync(`/proc/${pid}/cmdline`, 'utf8').includes('keepalive.js');
  } catch {
    return false;
  }
}

function mark(state) {
  if (!fs.existsSync(SOCKET)) return;
  // A hook passes its event as JSON on stdin; by hand, pass a session name instead.
  const session = process.argv[3] || JSON.parse(fs.readFileSync(0, 'utf8')).session_id;
  fs.mkdirSync(SESSIONS, { recursive: true });
  fs.writeFileSync(path.join(SESSIONS, path.basename(session)), state);
  if (!daemonRunning()) {
    spawn(process.execPath, [__filename, 'run'], { detached: true, stdio: 'ignore' }).unref();
  }
}

function working() {
  // Claude Code runs every shell command through a snapshot of the user's shell, in the foreground or not.
  const shell = spawnSync('pgrep', ['-f', '\\.claude/shell-snapshots/']).status === 0;
  return fs.readdirSync(SESSIONS).some((name) => {
    const file = path.join(SESSIONS, name);
    const quiet = age(file);
    if (quiet > BACKGROUND) {
      fs.rmSync(file);
      return false;
    }
    const busy = fs.readFileSync(file, 'utf8') === 'busy';
    return (busy && quiet < QUIET_TURN) || shell;
  });
}

function heartbeat() {
  // A gRPC call by hand: a protobuf of two strings (client id, activity) behind a 5-byte length prefix.
  const field = (tag, text) => Buffer.concat([Buffer.from([tag, text.length]), Buffer.from(text)]);
  const message = Buffer.concat([field(0x0a, 'claude-code'), field(0x12, 'working')]);
  const prefix = Buffer.alloc(5);
  prefix.writeUInt32BE(message.length, 1);
  return new Promise((resolve) => {
    const session = http2.connect('http://codespace-host', { createConnection: () => net.connect(SOCKET) });
    const done = (accepted) => {
      session.destroy();
      resolve(accepted);
    };
    session.on('error', () => done(false));
    session.setTimeout(10_000, () => done(false));
    const request = session.request({
      ':method': 'POST',
      ':path': RPC,
      'content-type': 'application/grpc',
      te: 'trailers',
      authorization: 'Bearer token', // the agent wants the header, not a real token; `gh` sends this too
    });
    const chunks = [];
    request.on('data', (chunk) => chunks.push(chunk));
    request.on('error', () => done(false));
    // The reply is one bool field, `result`: bytes 08 01 when the agent took the activity.
    request.on('end', () => done(Buffer.concat(chunks).subarray(5).equals(Buffer.from([0x08, 0x01]))));
    request.end(Buffer.concat([prefix, message]));
  });
}

async function run() {
  fs.writeFileSync(PIDFILE, String(process.pid));
  log('keeping the codespace awake');
  while (working()) {
    if (!(await heartbeat())) log('heartbeat not accepted');
    await new Promise((resolve) => setTimeout(resolve, MINUTE));
  }
  log('nothing is working; the idle timeout takes over');
  fs.rmSync(PIDFILE, { force: true });
}

async function status() {
  if (!fs.existsSync(SOCKET)) return console.log('not in a codespace');
  const sessions = fs.existsSync(SESSIONS) ? fs.readdirSync(SESSIONS) : [];
  for (const name of sessions) {
    const file = path.join(SESSIONS, name);
    console.log(`session ${name}: ${fs.readFileSync(file, 'utf8')}, ${Math.round(age(file) / MINUTE)} min ago`);
  }
  console.log(`working: ${sessions.length > 0 && working()}`);
  console.log(`daemon: ${daemonRunning() ? 'running' : 'stopped'}`);
  console.log(`heartbeat: ${(await heartbeat()) ? 'accepted' : 'not accepted'}`);
}

const commands = { busy: () => mark('busy'), idle: () => mark('idle'), run, status };
const command = commands[process.argv[2]];
if (!command) {
  console.error('usage: keepalive.js busy|idle|run|status');
  process.exit(1);
}
command();
