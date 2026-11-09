"""Preregistration Amendment 2: one sealed-test look for the calculation intervention.

`confirm.py run` picks the config by the amendment's dev rule, runs it once on test and grades it.
`confirm.py analyze` pairs it with r1a on test (needs final.py run to have graded r1a/test).
"""
import json, sys
import grade, stats, subject
from cli import ROOT
from final import graded

OUT = ROOT / "runs/confirm.json"


def pick():
    res = json.loads((ROOT / "runs/explore/calc/result.json").read_text())
    ok = [r for r in res if "dev" in r]
    best = max(ok, key=lambda r: r["dev"]["diff"])
    assert best["dev"]["lo_one_sided"] > 0, "no calculation candidate passed the dev gate"
    return best["name"], res


def run():
    name, _ = pick()
    print("confirming", name, flush=True)
    for _ in range(2):
        subject.run_split(name, "test", workers=4)
    grade.grade_run(name, "test")


def analyze():
    name, res = pick()
    a, b = graded("r1a", "test"), graded(name, "test")
    ids = sorted(set(a) & set(b))
    assert len(ids) == 240, f"only {len(ids)} paired test items"
    move = stats.mcnemar([a[i]["move_ok"] for i in ids], [b[i]["move_ok"] for i in ids])
    out = {"config": name, "dev": {r["name"]: r.get("dev") for r in res},
           "test": stats.paired([a[i]["score"] for i in ids], [b[i]["score"] for i in ids]),
           "test_means": {"r1a": stats.boot_mean([a[i]["score"] for i in ids]),
                          name: stats.boot_mean([b[i]["score"] for i in ids])},
           "move": move,
           "move_rate": {"r1a": sum(a[i]["move_ok"] for i in ids) / len(ids),
                         name: sum(b[i]["move_ok"] for i in ids) / len(ids)},
           "rating": {"r1a": stats.puzzle_rating([a[i]["rating"] for i in ids], [a[i]["move_ok"] for i in ids]),
                      name: stats.puzzle_rating([b[i]["rating"] for i in ids], [b[i]["move_ok"] for i in ids])},
           "subject_aiu_mean": {t: sum(g[i]["subject_aiu"] or 0 for i in ids) / len(ids)
                                for t, g in (("r1a", a), (name, b))}}
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    {"run": run, "analyze": analyze}[sys.argv[1]]()
