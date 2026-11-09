"""The grader: deterministic checks against the human-played solution, plus a rubric judge for the prose.

Score (0-100) = move 40 + line 15 + motif 15 + explanation 30.
"""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import chess
from cli import ROOT, make_home, run
from data import MOTIFS

JUDGE_MODEL = "gpt-5.6-luna"
W = {"move": 40, "line": 15, "motif": 15, "explanation": 30}

JUDGE = """You are grading a chess coaching note written for a club player (about 1500). Grade only against the facts below; they are verified by a chess library and by the game's actual solution.

FACTS
Position (FEN): {fen}
{board}
{side} to move; the opponent just played {last}.
Correct solution line (the only clearly winning continuation): {solution}
Tactical themes tagged for this position: {themes}
The coach's chosen move: {move} ({verdict})

COACHING NOTE TO GRADE
<<<
{note}
>>>

RUBRIC (score each 0, 1 or 2)
- accurate: every concrete claim about pieces, squares, attacks and moves is true in this position. 2 = no false claims; 1 = one minor slip that does not change the idea; 0 = recommends a wrong move, or contains a false claim that changes the idea.
- why: explains why the move works: the concrete threat and why the opponent cannot meet it. 2 = clear and correct; 1 = gestures at it or is partly right; 0 = missing or wrong.
- teach: the player could recognise this pattern in a future game from the note. 2 = names a transferable cue (what to look for); 1 = vague; 0 = none or misleading.

Reply with only a JSON object: {{"accurate": n, "why": n, "teach": n, "reason": "<one sentence>"}}"""


def parse_answer(text):
    blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S) or re.findall(r"(\{[^{}]*\"move\"[^{}]*\})", text, re.S)
    for blk in reversed(blocks):
        try:
            return json.loads(blk)
        except json.JSONDecodeError:
            continue
    return None


def note_of(text):
    return re.sub(r"```(?:json)?\s*\{.*?\}\s*```", "", text, flags=re.S).strip()


def _parse_move(b, s):
    s = str(s).strip().rstrip("!?")
    s = re.sub(r"^\d+\.(\.\.)?\s*", "", s)
    try:
        return b.parse_san(s)
    except ValueError:
        try:
            m = chess.Move.from_uci(s)
            return m if m in b.legal_moves else None
        except ValueError:
            return None


def deterministic(item, final):
    b = chess.Board(item["fen"])
    ans = parse_answer(final) or {}
    res = {"parsed": bool(ans), "move_ok": False, "line_legal": False, "line_frac": 0.0, "motif_ok": False, "move_san": None}
    m = _parse_move(b, ans.get("move", "")) if ans else None
    if m:
        res["move_san"] = b.san(m)
        bb = b.copy(); bb.push(m)
        res["move_ok"] = m.uci() == item["solution_uci"][0] or bb.is_checkmate()
    line = ans.get("line") if isinstance(ans.get("line"), list) else []
    if line and m and _parse_move(b, line[0]) != m:
        line = [ans.get("move")] + line
    bb, legal, match, ok_prefix = b.copy(), True, 0, True
    sol = item["solution_uci"]
    for i, s in enumerate(line[:8]):
        mv = _parse_move(bb, s)
        if mv is None:
            legal = False
            break
        if ok_prefix and i < len(sol) and mv.uci() == sol[i]:
            match += 1
        elif ok_prefix and i < len(sol):
            bb2 = bb.copy(); bb2.push(mv)
            if bb2.is_checkmate() and i % 2 == 0:
                match = len(sol)
            ok_prefix = False
        bb.push(mv)
    res["line_legal"] = bool(line) and legal
    res["line_frac"] = (match / len(sol)) if res["line_legal"] else 0.0
    picked = ans.get("motifs") if isinstance(ans.get("motifs"), list) else []
    themes = set(item["themes"])
    res["motif_ok"] = any(p in MOTIFS and MOTIFS[p] & themes for p in picked[:2])
    return res


def judge_prompt(item, final, det):
    b = chess.Board(item["fen"])
    sol, bb = [], b.copy()
    for u in item["solution_uci"]:
        mv = chess.Move.from_uci(u); sol.append(bb.san(mv)); bb.push(mv)
    pieces = "\n".join(f"{'White' if c else 'Black'}: " + ", ".join(
        f"{chess.piece_name(p.piece_type)} {chess.square_name(s)}" for s, p in b.piece_map().items() if p.color == c)
        for c in (True, False))
    verdict = "matches the solution" if det["move_ok"] else ("legal but NOT the solution" if det["move_san"] else "missing or illegal")
    return JUDGE.format(fen=item["fen"], board=pieces, side="White" if b.turn else "Black", last=item["last_move"],
                        solution=" ".join(sol), themes=", ".join(item["themes"]), move=det["move_san"] or "none",
                        verdict=verdict, note=note_of(final)[:2500] or "(empty)")


def parse_judge(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        j = json.loads(m.group(0))
        return {k: max(0, min(2, int(j[k]))) for k in ("accurate", "why", "teach")} | {"reason": j.get("reason", "")}
    except Exception:
        return None


def score(det, jd):
    expl = (jd["accurate"] + jd["why"] + jd["teach"]) / 6 if jd else 0.0
    return round(W["move"] * det["move_ok"] + W["line"] * det["line_frac"] + W["motif"] * det["motif_ok"]
                 + W["explanation"] * expl, 2)


def grade_run(tag, split, workers=8, judge_tag="judge", judge_model=None, ids=None):
    items = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / f"data/{split}.jsonl")}
    sdir = ROOT / "runs/subject" / tag / split
    gdir = ROOT / "runs/graded" / judge_tag / tag / split
    gdir.mkdir(parents=True, exist_ok=True)
    home, _ = make_home(ROOT / "runs/homes/_judge")

    def one(path):
        rec = json.loads(path.read_text())
        it = items[rec["id"]]
        det = deterministic(it, rec["final"])
        jd = None
        for _ in range(2):
            jr = run(judge_prompt(it, rec["final"], det), home, [], judge_model or JUDGE_MODEL, timeout=180)
            jd = parse_judge(jr["final"])
            if jd:
                break
        out = {"id": rec["id"], **det, "judge": jd, "score": score(det, jd), "judge_aiu": jr.get("aiu"),
               "subject_aiu": rec.get("aiu"), "tool_calls": len(rec["tool_calls"]), "rating": it["rating"],
               "motifs": it["motifs"]}
        (gdir / path.name).write_text(json.dumps(out))
        return out

    todo = [p for p in sorted(sdir.glob("*.json")) if not (gdir / p.name).exists() and (ids is None or p.stem in ids)]
    with ThreadPoolExecutor(workers) as ex:
        for i, f in enumerate(as_completed([ex.submit(one, p) for p in todo]), 1):
            r = f.result()
            print(f"[grade {tag}/{split}] {i}/{len(todo)} {r['id']} score={r['score']} move={r['move_ok']}", flush=True)


if __name__ == "__main__":
    grade_run(sys.argv[1], sys.argv[2], judge_tag=sys.argv[3] if len(sys.argv) > 3 else "judge")
