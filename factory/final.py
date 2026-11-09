"""Final, preregistered analysis. Run once, after the climb: `final.py run` then `final.py analyze`."""
import json, random, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
import grade, stats, subject
from cli import ROOT

STATE = ROOT / "runs/climb/state.json"
BARE = "v0-bare"
SECOND_JUDGE = "claude-sonnet-5"
N_REJUDGE = 80


def final_config():
    return json.loads(STATE.read_text())["incumbent"]


def graded(tag, split, judge_tag="judge"):
    d = ROOT / "runs/graded" / judge_tag / tag / split
    return {p.stem: json.loads(p.read_text()) for p in d.glob("*.json")}


def rejudge_ids():
    ids = sorted(json.loads(l)["id"] for l in open(ROOT / "data/test.jsonl"))
    return set(random.Random(20261108).sample(ids, N_REJUDGE))


def ensure(config, split, tag=None):
    tag = tag or config
    for _ in range(2):
        subject.run_split(config, split, tag, workers=6)
    grade.grade_run(tag, split)


def run():
    fin = final_config()
    jobs = [(BARE, "test"), (BARE, "test_mirror"), (fin, "test"), (fin, "test_mirror"), (fin, "dev", f"{fin}-aa")]
    with ThreadPoolExecutor(3) as ex:
        list(ex.map(lambda j: ensure(*j), jobs))
    ids = rejudge_ids()
    for tag in (BARE, fin):
        grade.grade_run(tag, "test", judge_tag="judge-retest", ids=ids)
        grade.grade_run(tag, "test", judge_tag="judge-second", judge_model=SECOND_JUDGE, ids=ids)


def det_score(g):
    return g["score"] - (grade.W["explanation"] * sum(g["judge"][k] for k in ("accurate", "why", "teach")) / 6 if g["judge"] else 0)


def expl(g):
    return sum(g["judge"][k] for k in ("accurate", "why", "teach")) if g["judge"] else None


def compare(a, b, key=lambda g: g["score"]):
    ids = sorted(set(a) & set(b))
    return stats.paired([key(a[i]) for i in ids], [key(b[i]) for i in ids])


def summary(g):
    v = list(g.values())
    k = sum(x["move_ok"] for x in v)
    return {"n": len(v), "score": stats.boot_mean([x["score"] for x in v]),
            "move_acc": stats.wilson(k, len(v)), "move_k": k,
            "det": stats.boot_mean([det_score(x) for x in v]),
            "expl_pts": stats.boot_mean([expl(x) for x in v if x["judge"]]),
            "judge_missing": sum(1 for x in v if not x["judge"]),
            "rating": stats.puzzle_rating([x["rating"] for x in v], [x["move_ok"] for x in v]),
            "tool_calls_mean": float(np.mean([x["tool_calls"] for x in v])),
            "subject_aiu_mean": float(np.mean([x["subject_aiu"] or 0 for x in v]))}


def unmirror(g):
    return {k[:-1]: v for k, v in g.items()}


def agreement(a, b):
    ids = sorted(i for i in set(a) & set(b) if a[i]["judge"] and b[i]["judge"])
    x, y = np.array([expl(a[i]) for i in ids], float), np.array([expl(b[i]) for i in ids], float)
    from scipy.stats import spearmanr
    return {"n": len(ids), "spearman": float(spearmanr(x, y).statistic), "mean_abs_diff_pts": float(np.abs(x - y).mean()),
            "exact": float((x == y).mean()), "mean_a": float(x.mean()), "mean_b": float(y.mean())}


def total_aiu():
    tot = {"subject": 0.0, "judge": 0.0, "teacher": 0.0}
    for p in (ROOT / "runs/subject").glob("*/*/*.json"):
        tot["subject"] += json.loads(p.read_text()).get("aiu") or 0
    for p in (ROOT / "runs/graded").glob("*/*/*/*.json"):
        tot["judge"] += json.loads(p.read_text()).get("judge_aiu") or 0
    for p in [*(ROOT / "runs/climb").glob("round*/teacher_aiu.txt"), *(ROOT / "runs/explore").glob("*/teacher_aiu.txt")]:
        try:
            tot["teacher"] += float(p.read_text())
        except ValueError:
            pass
    tot["total"] = sum(tot.values())
    return tot


def analyze():
    fin = final_config()
    state = json.loads(STATE.read_text())
    bt, bm, ft, fm = graded(BARE, "test"), unmirror(graded(BARE, "test_mirror")), graded(fin, "test"), unmirror(graded(fin, "test_mirror"))
    bd, fd, fa = graded(BARE, "dev"), graded(fin, "dev"), graded(f"{fin}-aa", "dev")
    ids = sorted(set(bt) & set(ft))
    mc = stats.mcnemar([bt[i]["move_ok"] for i in ids], [ft[i]["move_ok"] for i in ids])
    aa_ids = sorted(set(fd) & set(fa))
    rs = {
        "final": fin,
        "summary": {"bare_test": summary(bt), "final_test": summary(ft), "bare_mirror": summary(bm),
                    "final_mirror": summary(fm), "bare_dev": summary(bd), "final_dev": summary(fd), "final_dev_aa": summary(fa)},
        "primary": compare(bt, ft),
        "primary_item_diffs": [ft[i]["score"] - bt[i]["score"] for i in ids],
        "primary_mirror": compare(bm, fm),
        "deterministic_only": compare(bt, ft, det_score),
        "move_acc_diff": compare(bt, ft, lambda g: 100 * g["move_ok"]),
        "mcnemar": mc,
        "memorisation": {"bare": compare(bt, bm), "final": compare(ft, fm)},
        "aa": compare(fd, fa) | {"item_diffs": [fa[i]["score"] - fd[i]["score"] for i in aa_ids]},
        "dev_gain": compare(bd, fd),
        "judge": {
            "retest_final": agreement(ft, graded(fin, "test", "judge-retest")),
            "retest_bare": agreement(bt, graded(BARE, "test", "judge-retest")),
            "second_final": agreement(ft, graded(fin, "test", "judge-second")),
            "second_bare": agreement(bt, graded(BARE, "test", "judge-second")),
            "primary_under_second": compare(graded(BARE, "test", "judge-second"), graded(fin, "test", "judge-second")),
            "primary_same_subsample": compare({i: bt[i] for i in graded(BARE, "test", "judge-second")},
                                              {i: ft[i] for i in graded(fin, "test", "judge-second")}),
        },
        "rating_points": {"bare": [[bt[i]["rating"], bt[i]["move_ok"]] for i in ids],
                          "final": [[ft[i]["rating"], ft[i]["move_ok"]] for i in ids]},
        "by_motif": {},
        "climb": state["history"],
        "aiu": total_aiu(),
    }
    for m in sorted({mm for i in ids for mm in bt[i]["motifs"]}):
        sub = [i for i in ids if m in bt[i]["motifs"]]
        rs["by_motif"][m] = {"n": len(sub), "bare": sum(bt[i]["move_ok"] for i in sub), "final": sum(ft[i]["move_ok"] for i in sub)}
    (ROOT / "runs/results.json").write_text(json.dumps(rs, indent=2))
    print(json.dumps({k: rs[k] for k in ("final", "primary", "primary_mirror", "deterministic_only", "mcnemar", "memorisation", "aa", "dev_gain", "aiu")}
                     | {"aa": {k: v for k, v in rs["aa"].items() if k != "item_diffs"}}, indent=1))
    for k, v in rs["summary"].items():
        print(k, v["n"], "score", [round(x, 1) for x in v["score"]], "move", v["move_k"], [round(x, 3) for x in v["move_acc"]],
              "rating", [round(x) for x in v["rating"]], "judge_missing", v["judge_missing"])
    print(json.dumps(rs["judge"], indent=1))


if __name__ == "__main__":
    {"run": run, "analyze": analyze}[sys.argv[1]]()
