"""The system under test: a Copilot CLI agent, optionally adapted with a skill and chess-eyes tools."""
import json, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import chess
from cli import ROOT, make_home, run

SUBJECT_MODEL = "claude-haiku-4.5"
MOTIF_LIST = ("fork, pin, skewer, discoveredAttack, doubleCheck, deflection, attraction, sacrifice, hangingPiece, "
              "trappedPiece, promotion, intermezzo, clearance, interference, xRayAttack, quietMove, zugzwang, "
              "backRankMate, mate")

PROMPT = """A club player (rated about 1500) shows you a position from one of their own online games and asks what they missed.

Position (FEN): {fen}
{side} to move. {opp} just played {last}.

There is one clearly best move here. Find it, then write a short coaching note (at most 80 words) that explains the idea so the player can spot it next time.

End your reply with a JSON block exactly like this:
```json
{{"move": "<best move in SAN>", "line": ["<SAN>", "<SAN>", "..."], "motifs": ["<one or two of: {motifs}>"]}}
```
"line" is the main continuation starting with your move, alternating sides, up to 6 moves.{extra}"""


def prompt_for(item, skill):
    b = chess.Board(item["fen"])
    side, opp = ("White", "Black") if b.turn else ("Black", "White")
    extra = "\n\nUse the chess-coach skill." if skill else ""
    return PROMPT.format(fen=item["fen"], side=side, opp=opp, last=item["last_move"], motifs=MOTIF_LIST, extra=extra)


def load_config(name):
    d = ROOT / "configs" / name
    skill = (d / "SKILL.md").read_text() if (d / "SKILL.md").exists() else None
    tools = [t for t in (d / "tools.txt").read_text().split() if t] if (d / "tools.txt").exists() else []
    return skill, tools


def run_split(config, split, run_tag=None, workers=8, limit=None):
    skill, tools = load_config(config)
    home, allowed = make_home(ROOT / "runs/homes" / config, skill, tools)
    tag = run_tag or config
    outdir = ROOT / "runs/subject" / tag / split
    outdir.mkdir(parents=True, exist_ok=True)
    items = [json.loads(l) for l in open(ROOT / f"data/{split}.jsonl")][:limit]
    todo = [it for it in items if not (outdir / f"{it['id']}.json").exists()]

    def one(it):
        rec = run(prompt_for(it, skill), home, allowed, SUBJECT_MODEL)
        rec["id"] = it["id"]
        if (rec["final"] or rec["exit"] == 0) and not rec["violations"]:
            (outdir / f"{it['id']}.json").write_text(json.dumps(rec))
        return rec

    with ThreadPoolExecutor(workers) as ex:
        for i, fut in enumerate(as_completed([ex.submit(one, it) for it in todo]), 1):
            r = fut.result()
            print(f"[{tag}/{split}] {i}/{len(todo)} {r['id']} {r['seconds']}s tools={len(r['tool_calls'])} aiu={r['aiu']}", flush=True)
    return outdir


if __name__ == "__main__":
    config, split = sys.argv[1], sys.argv[2]
    tag = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
    run_split(config, split, tag, limit=limit)
