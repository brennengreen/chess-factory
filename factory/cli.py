"""Run one headless Copilot CLI session in an isolated COPILOT_HOME and collect what happened."""
import json, os, shutil, subprocess, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv/bin/python"
SERVER = ROOT / "server/chess_eyes.py"


def make_home(path, skill=None, tools=()):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    shutil.copy(Path.home() / ".copilot/config.json", path / "config.json")
    if skill:
        (path / "skills/chess-coach").mkdir(parents=True, exist_ok=True)
        (path / "skills/chess-coach/SKILL.md").write_text(skill)
    servers = {}
    if tools:
        servers["chess-eyes"] = {"type": "local", "command": str(PY), "args": [str(SERVER)],
                                 "env": {"CHESS_EYES_TOOLS": ",".join(tools)}, "tools": ["*"]}
    (path / "mcp-config.json").write_text(json.dumps({"mcpServers": servers}))
    allowed = (["skill"] if skill else []) + [f"chess-eyes-{t}" for t in tools]
    return path, allowed


def run(prompt, home, allowed, model, effort=None, timeout=420):
    with tempfile.TemporaryDirectory() as cwd:
        usage = Path(cwd) / "usage.json"
        cmd = ["copilot", "-p", prompt, "--model", model, "--no-custom-instructions", "--disable-builtin-mcps",
               "--allow-all-tools", "--no-ask-user", "--no-auto-update", "--output-format", "json",
               "--usage-output-file", str(usage), "--available-tools", *(allowed or [""])]
        if effort:
            cmd += ["--reasoning-effort", effort]
        env = dict(os.environ, COPILOT_HOME=str(home))
        t0 = time.time()
        try:
            p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
            out, err = p.stdout, p.returncode
        except subprocess.TimeoutExpired as e:
            out, err = (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "timeout"
        rec = {"seconds": round(time.time() - t0, 1), "exit": err, "final": "", "tool_calls": [], "aiu": None}
        for line in out.splitlines():
            if not line.startswith("{"):
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            d = e.get("data") or {}
            if e.get("type") == "assistant.message" and d.get("content"):
                rec["final"] = d["content"]
            elif e.get("type") == "tool.execution_start":
                rec["tool_calls"].append({"tool": d.get("toolName"), "args": d.get("arguments")})
        if usage.exists():
            u = json.loads(usage.read_text())
            rec["aiu"] = u.get("totalNanoAiu", 0) / 1e9
        return rec
