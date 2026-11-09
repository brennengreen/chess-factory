"""Exploratory climbability analysis (not part of the preregistered confirmatory analysis).

Questions: why did the climb stall, and which factor binds: gate resolution, the teacher's step size,
or headroom the editable surface can reach?
"""
import importlib.util, json, sys
from pathlib import Path
import numpy as np
from scipy import stats as st
import chess
import sim, stats

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


def paired(a, b, ids, key=lambda r: r["score"]):
    return stats.paired([key(a[i]) for i in ids], [key(b[i]) for i in ids])


def flips(a, b, ids):
    return stats.mcnemar([a[i]["move_ok"] for i in ids], [b[i]["move_ok"] for i in ids])


def forcing_tool():
    spec = importlib.util.spec_from_file_location("chess_eyes", ROOT / "server/chess_eyes.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.forcing_lines


def tool_alone(ids):
    """What forcing_lines says on its own: is its top-ranked try the solution's first move?"""
    items = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT / "data/dev.jsonl")}
    fl, top = forcing_tool(), {}
    for i in ids:
        r = fl(items[i]["fen"])
        top[i] = r.split("\n")[1][2:].split(":")[0] if r.startswith("Forcing") else None
    return {i: top[i] == items[i]["solution_san"][0] for i in ids}, top


def cost(tag, split="dev"):
    v = [json.loads(p.read_text()).get("aiu") or 0 for p in (ROOT / "runs/subject" / tag / split).glob("*.json")]
    return float(np.mean(v)) if v else None


def main():
    state = json.loads((ROOT / "runs/climb/state.json").read_text())
    out = {"steps": []}
    for h in state["history"]:
        for c in h["candidates"]:
            if "dev" in c:
                out["steps"].append({"round": h["round"], "name": c["name"], "vs": h["incumbent"],
                                     "dev_mean": c["dev_mean"],
                                     **{k: c["dev"][k] for k in ("diff", "lo", "hi", "lo_one_sided", "sd_diff")}})
    climb_tags = ["v0-bare"] + [s["name"] for s in out["steps"]]
    extra = ["r1a-aa", "r1a+oracle-move", "x-minimal-a", "x-minimal-b", "x-calc-a", "x-calc-b"]
    data = {t: load(t) for t in climb_tags + extra}
    missing = {t: 120 - len(v) for t, v in data.items() if len(v) < 120}
    data = {t: v for t, v in data.items() if len(v) >= 119}
    ids = sorted(set.intersection(*[set(data[t]) for t in climb_tags if t in data]))
    r1 = data["r1a"]
    own = {t: sorted(set(v) & set(r1)) for t, v in data.items()}
    out["n_dev"], out["missing"] = len(ids), missing
    out["components"] = {t: components([v[i] for i in own[t]]) for t, v in data.items()}
    out["dev_mean"] = {t: stats.boot_mean([v[i]["score"] for i in own[t]]) for t, v in data.items()}
    out["cost_per_puzzle"] = {t: cost(t) for t in data}
    out["tool_calls_per_puzzle"] = {t: float(np.mean([v[i]["tool_calls"] for i in own[t]])) for t, v in data.items()}
    out["vs_r1a"] = {t: {**paired(r1, data[t], own[t]), "move": flips(r1, data[t], own[t])}
                     for t in data if t not in ("r1a", "v0-bare")}

    right = [r1[i] for i in ids if r1[i]["move_ok"]]
    out["r1a_given_right_move"] = {"n": len(right), "explanation_pts": float(np.mean([explanation_pts(r) for r in right])),
                                   **{k: float(np.mean([(r.get("judge") or {}).get(k, 0) for r in right]))
                                      for k in ("accurate", "why", "teach")}}

    # Noise budget. A/A: r1a rerun. Rejudge: same r1a outputs, judged again. Candidates: rounds 2-5.
    rj = load("r1a", judge="judge-retest")
    aa = out["vs_r1a"]["r1a-aa"]
    rjd = np.array([rj[i]["score"] - r1[i]["score"] for i in ids if i in rj])
    sd_c = float(np.sqrt(np.mean([s["sd_diff"] ** 2 for s in out["steps"] if s["round"] > 1])))
    se = aa["sd_diff"] / np.sqrt(2)
    sb = float(np.sqrt(max(sd_c ** 2 - aa["sd_diff"] ** 2, 0) / 2))
    out["noise"] = {"sd_diff_candidates": sd_c, "sd_diff_aa": aa["sd_diff"], "sd_rejudge": float(rjd.std(ddof=1)),
                    "rejudge_identical": float((rjd == 0).mean()), "run_sd_SE": float(se), "interaction_sd_SB": sb,
                    "share_run_to_run": float(aa["sd_diff"] ** 2 / sd_c ** 2),
                    "share_judge": float(rjd.var(ddof=1) / sd_c ** 2),
                    "mde_n120": mde(sd_c, 120), "mde_n480": mde(sd_c, 480),
                    "n_needed": {d: n_for(sd_c, d) for d in (2, 4, 6, 8, 10)}}

    # The operator's step distribution: true spread = observed spread minus sampling noise.
    def step_stats(names):
        d = np.array([out["vs_r1a"][n]["diff"] for n in names if n in out["vs_r1a"]])
        if not len(d):
            return {"names": names, "diffs": [], "mean": None, "sd": None, "tau": None}
        samp = sd_c / np.sqrt(len(ids))
        return {"names": names, "diffs": d.tolist(), "mean": float(d.mean()),
                "sd": float(d.std(ddof=1)) if len(d) > 1 else None,
                "tau": float(np.sqrt(max(d.var(ddof=1) - samp ** 2, 0))) if len(d) > 1 else None}
    out["operator"] = {"rewrites_r2_r5": step_stats([s["name"] for s in out["steps"] if s["round"] > 1]),
                       "minimal_edits": step_stats(["x-minimal-a", "x-minimal-b"]),
                       "calc_surface": step_stats(["x-calc-a", "x-calc-b"])}

    # Headroom: the oracle says how many points sit above r1a if the first move were found.
    if "x-calc-a" in data:
        ids = own["x-calc-a"]
        ok, top = tool_alone(ids)
        xc = data["x-calc-a"]
        calls = {i: json.loads((ROOT / "runs/subject/x-calc-a/dev" / f"{i}.json").read_text())["tool_calls"] for i in ids}
        used = {i: any("forcing_lines" in t["tool"] for t in calls[i]) for i in ids}
        out["headroom"] = {"oracle_gain": out["vs_r1a"]["r1a+oracle-move"]["diff"],
                           "calc_gain": out["vs_r1a"]["x-calc-a"]["diff"],
                           "recovered": out["vs_r1a"]["x-calc-a"]["diff"] / out["vs_r1a"]["r1a+oracle-move"]["diff"],
                           "tool_alone_first_move": sum(ok.values()), "calc_first_move": sum(xc[i]["move_ok"] for i in ids),
                           "calc_called_tool": sum(used.values()),
                           "calc_played_tool_top": sum(xc[i]["move_san"] == top[i] for i in ids),
                           "calc_beat_tool": sum(xc[i]["move_ok"] and not ok[i] for i in ids),
                           "tool_beat_calc": sum(ok[i] and not xc[i]["move_ok"] for i in ids),
                           "calc_given_right_move": {k: float(np.mean([(xc[i].get("judge") or {}).get(k, 0) for i in ids if xc[i]["move_ok"]]))
                                                     for k in ("accurate", "why", "teach")}}

    ids = sorted(set.intersection(*[set(data[t]) for t in climb_tags if t in data]))
    mv = np.array([[data[t][i]["move_ok"] for i in ids] for t in climb_tags[1:] if t in data], bool)
    out["move_by_item"] = {"always_solved": int(mv.all(0).sum()), "never_solved": int((~mv).all(0).sum()),
                           "configs": int(mv.shape[0])}

    # Simulated 5-round climbs under the measured noise, for a range of operator mean steps.
    tau = out["operator"]["rewrites_r2_r5"]["tau"] or 2.0
    out["sim"] = {"tau": tau, "SB": sb, "SE": float(se), "curves": {}}
    for n in (120, 480):
        out["sim"]["curves"][n] = [{"M": M, **sim.sweep(sims=600, seed=2000 + M * 7 + n, n=n, M=M, TAU=tau, SB=sb, SE=se)}
                                   for M in range(-10, 9)]
    (ROOT / "runs/explore.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps({k: out[k] for k in ("n_dev", "missing", "noise", "operator", "move_by_item")} |
                     {"headroom": out.get("headroom")}, indent=1, default=lambda x: round(float(x), 2)))


if __name__ == "__main__":
    main()
