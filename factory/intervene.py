"""Exploratory interventions after the preregistered climb (dev only; test is never touched).

Both use the same teacher input as climb round 5 (incumbent r1a's failures on train_r5), so each differs
from round 5 in exactly one factor:
  minimal  the operator: each candidate is a single small edit of r1a instead of a full rewrite
  calc     the surface: the tool catalog also offers forcing_lines, a calculation aid
"""
import json, sys
from pathlib import Path
import climb, stats, teacher, subject
from cli import ROOT

R3 = "3. Tools: you may only enable or disable tools from the catalog. Tools show the board; none of them search or evaluate, and none may be added that do. If a missing perception tool would clearly help, describe it under tool_request; a human decides whether to build it."
R5 = "5. Propose exactly two candidates that test different hypotheses about what is holding the score back."

VARIANTS = {
    "minimal": dict(prompt=teacher.PROMPT.replace(R5, (
        "5. Propose exactly two candidates. Each must be a MINIMAL edit of the CURRENT SKILL.md: copy it verbatim and "
        "change one thing only (add, replace or delete a single rule or step, at most 60 words), aimed at the largest "
        "weakness in the grader report. Keep the current tools unless your one change is enabling or disabling a "
        "single tool. The two candidates must make different single changes.")), catalog=teacher.TOOL_CATALOG),
    "calc": dict(prompt=teacher.PROMPT.replace(R3, (
        "3. Tools: you may only enable or disable tools from the catalog. Most tools only show the board; "
        "forcing_lines also calculates forcing sequences and reports their outcome. Do not request new tools.")),
        catalog={**teacher.TOOL_CATALOG, "forcing_lines": (
            "Calculation aid: searches the side to move's checks, captures and promotions against every defence, "
            "up to five plies, and reports the three best forcing tries with their main line and the material swing "
            "or mate. Quiet moves are not searched.")}),
}
assert all(VARIANTS[v]["prompt"] != teacher.PROMPT for v in VARIANTS)


def run(variant):
    v = VARIANTS[variant]
    out_dir = ROOT / "runs/explore" / variant
    split, inc = "train_r5", "r1a"
    graded = climb.ensure(inc, split)
    items = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / f"data/{split}.jsonl")}
    skill, tools = subject.load_config(inc)
    reply = out_dir / "teacher_reply.json"
    if reply.exists() and json.loads(reply.read_text()):
        out = json.loads(reply.read_text())
    else:
        out, _ = teacher.propose(skill, tools, list(graded.values()), items, ROOT / "runs/subject" / inc / split, 0,
                                 prompt_template=v["prompt"], catalog=v["catalog"], log=out_dir)
    inc_dev = climb.ensure(inc, "dev")
    res = []
    for k, cand in zip("ab", out["candidates"]):
        name = f"x-{variant}-{k}"
        leaks = teacher.leak_check(cand.get("skill_md", ""))
        d = ROOT / "configs" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(cand["skill_md"].strip() + "\n")
        (d / "tools.txt").write_text(" ".join(t for t in cand.get("tools", []) if t in v["catalog"]) + "\n")
        (d / "meta.json").write_text(json.dumps({k2: cand.get(k2) for k2 in ("hypothesis", "citations")}, indent=2))
        if leaks:
            res.append({"name": name, "leaks": leaks})
            continue
        dev = climb.ensure(name, "dev")
        ids = sorted(set(dev) & set(inc_dev))
        res.append({"name": name, "hypothesis": cand.get("hypothesis"), "tools": cand.get("tools"),
                    "dev": stats.paired([inc_dev[i]["score"] for i in ids], [dev[i]["score"] for i in ids])})
    (out_dir / "result.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=1), flush=True)


if __name__ == "__main__":
    run(sys.argv[1])
