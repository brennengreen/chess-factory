"""Monte Carlo model of a gated hill climb under noise (exploratory, for the post).

Per-item score of config c on item i, run r:  y = mu_c + a_i + b_ci + e_cir
  a_i   item difficulty (cancels in a paired comparison)
  b_ci  item x config interaction: real, repeatable churn (sd SB)
  e_cir run-to-run noise from subject sampling and the judge (sd SE)
A/A paired sd = sqrt(2) SE; config-vs-config paired sd = sqrt(2 SB^2 + 2 SE^2).

The teacher proposes K candidates per round with true step s ~ N(M, TAU). The gate accepts the best
candidate if the one-sided 95% lower bound of its paired dev gain is above zero.
"""
import json, sys
import numpy as np
from scipy import stats as st

Z = st.norm.ppf(.95)


def climb(rounds=5, n=120, K=2, M=0.0, TAU=6.0, SB=20.0, SE=20.0, refresh=False, reps=1, rng=None):
    rng = rng or np.random.default_rng()
    mu = 0.0
    b_inc = rng.normal(0, SB, n)
    e_inc = rng.normal(0, SE / np.sqrt(reps), n)
    accepted = false_acc = 0
    for _ in range(rounds):
        if refresh:
            e_inc = rng.normal(0, SE / np.sqrt(reps), n)
        best = None
        for _ in range(K):
            s = rng.normal(M, TAU)
            b = rng.normal(0, SB, n)
            e = rng.normal(0, SE / np.sqrt(reps), n)
            d = (mu + s + b + e) - (mu + b_inc + e_inc)
            lo = d.mean() - Z * d.std(ddof=1) / np.sqrt(n)
            if best is None or d.mean() > best[0]:
                best = (d.mean(), lo, s, b, e)
        if best[1] > 0:
            accepted += 1
            false_acc += best[2] <= 0
            mu += best[2]
            b_inc, e_inc = best[3], best[4]
    return mu, accepted, false_acc


def sweep(sims=2000, seed=0, **kw):
    rng = np.random.default_rng(seed)
    r = np.array([climb(rng=rng, **kw) for _ in range(sims)])
    return {"true_gain": float(r[:, 0].mean()), "accepts": float(r[:, 1].mean()),
            "false_accepts": float(r[:, 2].mean())}


def power(delta, sd, n):
    return float(1 - st.norm.cdf(Z - delta * np.sqrt(n) / sd))


SB, SE = 12.6, 21.0  # measured: config-vs-config paired sd 34.6, A/A paired sd 29.7


def grid(ns=(120, 480), Ms=tuple(range(-8, 9, 2)), taus=(0, 2, 4, 6, 8, 10), sims=400):
    out = []
    for n in ns:
        for M in Ms:
            for t in taus:
                r = sweep(sims=sims, seed=(M + 50) * 100 + t + n, n=n, M=M, TAU=t, SB=SB, SE=SE)
                out.append({"n": n, "M": M, "tau": t, **r})
    return out


if __name__ == "__main__":
    if sys.argv[1:] == ["grid"]:
        from pathlib import Path
        g = grid()
        Path(__file__).resolve().parents[1].joinpath("runs/sim_grid.json").write_text(json.dumps(g, indent=1))
        for row in g:
            print(row)
    else:
        print(json.dumps(sweep(SB=SB, SE=SE, **(json.loads(sys.argv[1]) if len(sys.argv) > 1 else {})), indent=1))
