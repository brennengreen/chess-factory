"""Hill climbing: teacher proposes, grader disposes, statistics decide.

Acceptance rule (fixed before the first round): a candidate replaces the incumbent only if its paired
improvement on dev has a one-sided 95% bootstrap lower bound above zero. Test is never touched here.
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import grade, stats, subject, teacher
from cli import ROOT

STATE = ROOT / "runs/climb/state.json"
TRAIN_SLICE = 60


def ensure(config, split, tag=None):
    tag = tag or config
    for _ in range(2):
        subject.run_split(config, split, tag)
    grade.grade_run(tag, split)
    gdir = ROOT / "runs/graded/judge" / tag / split
    return {json.loads(p.read_text())["id"]: json.loads(p.read_text()) for p in gdir.glob("*.json")}


def train_slice(r):
    items = [l for l in open(ROOT / "data/train.jsonl")]
    start = ((r - 1) * TRAIN_SLICE) % len(items)
    chunk = (items + items)[start:start + TRAIN_SLICE]
    (ROOT / f"data/train_r{r}.jsonl").write_text("".join(chunk))
    return f"train_r{r}"


def write_config(name, cand):
    d = ROOT / "configs" / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(cand["skill_md"].strip() + "\n")
    tools = [t for t in cand.get("tools", []) if t in teacher.TOOL_CATALOG]
    (d / "tools.txt").write_text(" ".join(tools) + "\n")
    (d / "meta.json").write_text(json.dumps({k: cand.get(k) for k in ("hypothesis", "citations")}, indent=2))


def main(rounds):
    state = json.loads(STATE.read_text()) if STATE.exists() else {"incumbent": "v0-bare", "history": []}
    done = {h["round"] for h in state["history"]}
    for r in range(1, rounds + 1):
        if r in done:
            continue
        inc = state["incumbent"]
        print(f"=== round {r}: incumbent {inc}", flush=True)
        inc_dev = ensure(inc, "dev")
        split = train_slice(r)
        train_graded = ensure(inc, split)
        items = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / f"data/{split}.jsonl")}
        skill, tools = subject.load_config(inc)
        out, passages = teacher.propose(skill, tools, list(train_graded.values()), items,
                                        ROOT / "runs/subject" / inc / split, r)
        entry = {"round": r, "incumbent": inc, "diagnosis": out and out.get("diagnosis"),
                 "tool_request": out and out.get("tool_request"), "passages": [p["id"] for p in passages],
                 "candidates": []}
        names = []
        for k, cand in zip("ab", (out or {}).get("candidates", [])):
            name = f"r{r}{k}"
            leaks = teacher.leak_check(cand.get("skill_md", ""))
            entry["candidates"].append({"name": name, "hypothesis": cand.get("hypothesis"), "tools": cand.get("tools"),
                                        "citations": cand.get("citations"), "leaks": leaks})
            if not leaks:
                write_config(name, cand)
                names.append(name)
        with ThreadPoolExecutor(2) as ex:
            devs = dict(zip(names, ex.map(lambda n: ensure(n, "dev"), names)))
        best = None
        for c in entry["candidates"]:
            if c["name"] not in devs:
                continue
            ids = sorted(set(devs[c["name"]]) & set(inc_dev))
            c["dev"] = stats.paired([inc_dev[i]["score"] for i in ids], [devs[c["name"]][i]["score"] for i in ids])
            c["dev_mean"] = stats.boot_mean([devs[c["name"]][i]["score"] for i in ids])
            if best is None or c["dev"]["diff"] > best["dev"]["diff"]:
                best = c
        entry["incumbent_dev_mean"] = stats.boot_mean([v["score"] for v in inc_dev.values()])
        entry["accepted"] = bool(best and best["dev"]["lo_one_sided"] > 0)
        if entry["accepted"]:
            state["incumbent"] = best["name"]
        entry["new_incumbent"] = state["incumbent"]
        state["history"].append(entry)
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(state, indent=2))
        print(json.dumps({k: entry[k] for k in ("round", "accepted", "new_incumbent")}),
              [(c["name"], c.get("dev", {}).get("diff"), c.get("dev", {}).get("lo_one_sided"), c["leaks"][:2]) for c in entry["candidates"]], flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 5)
