"""Exploratory climbability analysis (not part of the preregistered confirmatory analysis).

Questions: why did the climb stall, and which factor binds: gate resolution, the teacher's step size,
or headroom the editable surface can reach?
"""
import json, sys
from pathlib import Path
import numpy as np
from scipy import stats as st

ROOT = Path(__file__).resolve().parents[1]
G = ROOT / "runs/graded"


def load(tag, split="dev", judge="judge"):
    d = G / judge / tag / split
    return {p.stem: json.loads(p.read_text()) for p in d.glob("*.json")} if d.exists() else {}


def explanation_pts(r):
    j = r.get("judge") or {}
    return 30 * sum(j.get(k, 0) for k in ("accurate", "why", "teach")) / 6


def components(rs):
    n = len(rs)
    mv = sum(40 * r["move_ok"] for r in rs) / n
    ln = sum(15 * r["line_frac"] for r in rs) / n
    mo = sum(15 * r["motif_ok"] for r in rs) / n
    ex = sum(explanation_pts(r) for r in rs) / n
    return {"move": mv, "line": ln, "motif": mo, "explanation": ex, "total": mv + ln + mo + ex}


def mde(sd, n, alpha=.05, power=.8):
    return (st.norm.ppf(1 - alpha) + st.norm.ppf(power)) * sd / np.sqrt(n)


def n_for(sd, delta, alpha=.05, power=.8):
    return int(np.ceil(((st.norm.ppf(1 - alpha) + st.norm.ppf(power)) * sd / delta) ** 2))


def main():
    state = json.loads((ROOT / "runs/climb/state.json").read_text())
    out = {"steps": []}
    for h in state["history"]:
        for c in h["candidates"]:
            if "dev" in c:
                out["steps"].append({"round": h["round"], "name": c["name"], "vs": h["incumbent"],
                                     **{k: c["dev"][k] for k in ("diff", "lo", "hi", "lo_one_sided", "sd_diff")}})
    tags = ["v0-bare"] + [s["name"] for s in out["steps"]]
    data = {t: load(t) for t in tags}
    data = {t: v for t, v in data.items() if len(v) >= 120}
    ids = sorted(set.intersection(*[set(v) for v in data.values()]))
    out["n_dev"] = len(ids)
    out["components"] = {t: components([v[i] for i in ids]) for t, v in data.items()}

    r1 = data["r1a"]
    right = [r1[i] for i in ids if r1[i]["move_ok"]]
    wrong = [r1[i] for i in ids if not r1[i]["move_ok"]]
    out["r1a_expl_given_move"] = {"right": np.mean([explanation_pts(r) for r in right]),
                                  "wrong": np.mean([explanation_pts(r) for r in wrong]),
                                  "n_right": len(right)}
    out["r1a_judge_given_move_right"] = {k: np.mean([(r.get("judge") or {}).get(k, 0) for r in right])
                                         for k in ("accurate", "why", "teach")}

    tooled = [t for t in data if t != "v0-bare"]
    M = np.array([[data[t][i]["score"] for i in ids] for t in tooled])
    item_mean = M.mean(0)
    resid = M - item_mean - (M.mean(1, keepdims=True) - M.mean())
    out["variance"] = {"configs": tooled, "item_var": float(item_mean.var(ddof=1)),
                       "resid_var": float(resid.var(ddof=1) * M.size / (M.size - M.shape[0] - M.shape[1] + 1)),
                       "total_var": float(M.var(ddof=1))}
    out["variance"]["item_share"] = out["variance"]["item_var"] / (out["variance"]["item_var"] + out["variance"]["resid_var"])

    mv = np.array([[data[t][i]["move_ok"] for i in ids] for t in tooled], bool)
    always = int(mv.all(0).sum()); never = int((~mv).all(0).sum())
    out["move_by_item"] = {"always_solved": always, "never_solved": never, "sometimes": len(ids) - always - never,
                           "configs": len(tooled)}
    rating = np.array([r1[i]["rating"] for i in ids])
    out["never_solved_rating_mean"] = float(rating[(~mv).all(0)].mean())
    out["always_solved_rating_mean"] = float(rating[mv.all(0)].mean())

    sd = np.mean([s["sd_diff"] for s in out["steps"] if s["round"] > 1])
    out["gate"] = {"sd_diff_later_rounds": sd, "mde_n120": mde(sd, 120),
                   "n_needed": {d: n_for(sd, d) for d in (2, 4, 6, 8, 10)}}
    (ROOT / "runs/explore.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out, indent=1, default=lambda x: round(float(x), 2)))


if __name__ == "__main__":
    main()
