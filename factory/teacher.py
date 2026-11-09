"""The teacher: turns the grader's failures on the TRAIN split into cited, general skill revisions.

It never sees dev or test items. Its proposals are scanned for leaked positions before they are tested.
"""
import collections, json, re
import chess
from cli import ROOT, make_home, run
from corpus import Library
from grade import note_of

TEACHER_MODEL = "claude-opus-5.5"
TOOL_CATALOG = {
    "board": "Draw the position: diagram, piece list for each side, side to move, check status, material.",
    "legal_moves": "List every legal move for the side to move, grouped into checks, captures and quiet moves.",
    "threats": "Report loose pieces (attacked and undefended, or attacked by a cheaper piece) and pins, for both sides.",
    "inspect_move": "Play one move and describe the result: check or mate, what the moved piece attacks, newly loose "
                    "pieces, the opponent's checks and captures in reply, and the resulting FEN to keep exploring.",
    "square_info": "Who controls one square: the piece on it, every attacker and defender of each side, and x-ray "
                   "attackers lined up behind exactly one blocking piece. (Built after the round 1 tool_request.)",
    "line_view": "What one piece sees: for a rook, bishop or queen, the first piece along each line and the piece "
                 "behind it (pins, x-rays, discovered attacks); for a knight, king or pawn, the pieces it touches. "
                 "(Built after the round 2 tool_request.)",
}

PROMPT = """You are the teacher in a teacher/grader pair. A small model coaches club chess players: given a position it must find the one clearly best move, give the main line, name the motif, and explain the idea. A grader scores it (move 40, line 15, motif 15, explanation 30). Your job is to propose revisions to the model's SKILL.md and its tool set that will raise the score on positions you will never see.

RULES (a revision that breaks one is rejected unseen)
1. Teach transferable method, the way a human coach would. Never mention a specific position, FEN, square sequence or move from the examples below. They come from a training split; the evaluation positions are different.
2. Ground each principle in the human sources below and cite passage IDs like [P0123]. Do not invent chess theory.
3. Tools: you may only enable or disable tools from the catalog. Tools show the board; none of them search or evaluate, and none may be added that do. If a missing perception tool would clearly help, describe it under tool_request; a human decides whether to build it.
4. SKILL.md must start with YAML front matter (name: chess-coach, description: ...) and stay under 600 words.
5. Propose exactly two candidates that test different hypotheses about what is holding the score back.

CURRENT SKILL.md
<<<
{skill}
>>>
Tools currently enabled: {tools}

TOOL CATALOG
{catalog}

GRADER REPORT ON {n} TRAINING POSITIONS
{report}

FAILED TRAINING EXAMPLES (for diagnosis only, never quote them)
{examples}

HUMAN SOURCES (retrieved for these failures)
{passages}

Reply with only JSON:
{{"diagnosis": "<what is going wrong, 2-3 sentences>",
 "candidates": [{{"hypothesis": "<one sentence>", "tools": ["..."], "skill_md": "<full SKILL.md>", "citations": ["P...."]}}, {{...}}],
 "tool_request": "<optional: a perception tool you wish existed, or empty>"}}"""


def report(graded, subject_dir):
    n = len(graded)
    g = graded
    lines = [f"Mean score {sum(x['score'] for x in g) / n:.1f}/100. Correct move {sum(x['move_ok'] for x in g)}/{n}. "
             f"Answer unparseable {sum(not x['parsed'] for x in g)}. Line legal {sum(x['line_legal'] for x in g)}/{n}. "
             f"Motif named correctly {sum(x['motif_ok'] for x in g)}/{n}. Mean tool calls {sum(x['tool_calls'] for x in g) / n:.1f}."]
    j = [x["judge"] for x in g if x["judge"]]
    if j:
        lines.append("Judge means (0-2): " + ", ".join(f"{k} {sum(x[k] for x in j) / len(j):.2f}" for k in ("accurate", "why", "teach")))
    right_bad_note = sum(1 for x in g if x["move_ok"] and x["judge"] and x["judge"]["accurate"] == 0)
    lines.append(f"Right move but inaccurate explanation: {right_bad_note}.")
    by = collections.defaultdict(list)
    for x in g:
        for m in x["motifs"]:
            by[m].append(x["move_ok"])
    lines.append("Correct move by tagged motif: " + ", ".join(f"{m} {sum(v)}/{len(v)}" for m, v in sorted(by.items(), key=lambda kv: -len(kv[1]))))
    band = collections.defaultdict(list)
    for x in g:
        band[(x["rating"] // 300) * 300].append(x["move_ok"])
    lines.append("Correct move by human puzzle rating: " + ", ".join(f"{b}-{b + 299}: {sum(v)}/{len(v)}" for b, v in sorted(band.items())))
    tools = collections.Counter()
    for x in g:
        rec = json.loads((subject_dir / f"{x['id']}.json").read_text())
        tools.update(t["tool"] for t in rec["tool_calls"])
    lines.append("Tool calls in total: " + (", ".join(f"{k} {v}" for k, v in tools.most_common()) or "none"))
    return "\n".join(lines)


def examples(graded, items, subject_dir, k=6):
    bad = sorted([x for x in graded if x["score"] < 60], key=lambda x: x["score"])[:k]
    out = []
    for x in bad:
        it = items[x["id"]]
        rec = json.loads((subject_dir / f"{x['id']}.json").read_text())
        b = chess.Board(it["fen"])
        out.append(f"- FEN {it['fen']} ({'White' if b.turn else 'Black'} to move, human puzzle rating {it['rating']}, themes {', '.join(it['themes'])})\n"
                   f"  Model played {x['move_san']}; solution {' '.join(it['solution_san'])}. Tools used: "
                   f"{', '.join(t['tool'].replace('chess-eyes-', '') for t in rec['tool_calls']) or 'none'}.\n"
                   f"  Judge: {(x['judge'] or {}).get('reason', 'n/a')}\n  Model's note: {note_of(rec['final'])[:400]!r}")
    return "\n".join(out)


def retrieve(lib, graded, k_total=10):
    weak = collections.Counter()
    for x in graded:
        if not x["move_ok"]:
            weak.update(x["motifs"])
    queries = ["calculate every check capture and threat before choosing a move, forcing moves",
               "explain why the move works and what the opponent cannot prevent"]
    queries += [f"{m} tactic how to recognise and exploit" for m, _ in weak.most_common(4)]
    seen, out = set(), []
    for q in queries:
        for d in lib.search(q, 3):
            if d["id"] not in seen and len(out) < k_total:
                seen.add(d["id"]); out.append(d)
    return out


def leak_check(text, splits=("train", "dev", "test", "test_mirror")):
    """Reject any skill that carries a position, puzzle id, or two-move solution sequence from any split."""
    hits = []
    for s in splits:
        for line in open(ROOT / f"data/{s}.jsonl"):
            it = json.loads(line)
            if it["fen"].split()[0] in text or re.search(rf"\b{re.escape(it['id'])}\b", text):
                hits.append(f"{s}:{it['id']}:position")
            sol = it["solution_san"]
            for i in range(len(sol) - 1):
                if f"{sol[i]} {sol[i + 1]}" in text:
                    hits.append(f"{s}:{it['id']}:line {sol[i]} {sol[i + 1]}")
    return hits


def propose(skill, tools, graded, items, subject_dir, round_no):
    lib = Library()
    passages = retrieve(lib, graded)
    prompt = PROMPT.format(
        skill=skill or "(none: the model has no skill yet)", tools=", ".join(tools) or "none",
        catalog="\n".join(f"- {k}: {v}" for k, v in TOOL_CATALOG.items()), n=len(graded),
        report=report(graded, subject_dir), examples=examples(graded, items, subject_dir),
        passages="\n\n".join(f"[{d['id']}] {d['source']}: {d['text']}" for d in passages))
    home, _ = make_home(ROOT / "runs/homes/_teacher")
    for attempt in range(3):
        r = run(prompt, home, [], TEACHER_MODEL, timeout=600)
        m = re.search(r"\{.*\}", r["final"], re.S)
        try:
            out = json.loads(m.group(0))
            assert len(out["candidates"]) == 2
            break
        except Exception:
            out = None
    log = ROOT / f"runs/climb/round{round_no}"
    log.mkdir(parents=True, exist_ok=True)
    (log / "teacher_prompt.txt").write_text(prompt)
    (log / "teacher_reply.json").write_text(json.dumps(out, indent=2))
    (log / "teacher_aiu.txt").write_text(str(r.get("aiu")))
    return out, passages
