"""Statistics for defending a claim: bootstrap CIs, paired tests, Wilson intervals, and a puzzle-rating MLE."""
import math
import numpy as np
from scipy import stats as st
from scipy.optimize import minimize_scalar

B = 10000


def boot_mean(x, seed=0, alpha=0.05):
    x = np.asarray(x, float)
    rng = np.random.default_rng(seed)
    m = x[rng.integers(0, len(x), (B, len(x)))].mean(1)
    return float(x.mean()), float(np.quantile(m, alpha / 2)), float(np.quantile(m, 1 - alpha / 2))


def paired(a, b, seed=0):
    """Mean of b - a with a 95% bootstrap CI, the one-sided 5% lower bound, and a Wilcoxon p-value."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    rng = np.random.default_rng(seed)
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    nz = d[d != 0]
    p = float(st.wilcoxon(nz).pvalue) if len(nz) > 0 else 1.0
    return {"diff": float(d.mean()), "lo": float(np.quantile(m, .025)), "hi": float(np.quantile(m, .975)),
            "lo_one_sided": float(np.quantile(m, .05)), "p_wilcoxon": p, "n": len(d),
            "sd_diff": float(d.std(ddof=1))}


def wilson(k, n, z=1.96):
    if n == 0:
        return 0, 0, 0
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return p, c - h, c + h


def mcnemar(a, b):
    """Exact McNemar test on paired booleans."""
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    n01, n10 = int((~a & b).sum()), int((a & ~b).sum())
    p = float(st.binomtest(min(n01, n10), n01 + n10, 0.5).pvalue) if n01 + n10 else 1.0
    return {"gained": n01, "lost": n10, "p": p}


def puzzle_rating(ratings, correct, seed=0):
    """MLE of the Lichess-style rating P at which P(solve) = 1 / (1 + 10^((R - P) / 400)) fits the outcomes."""
    r, c = np.asarray(ratings, float), np.asarray(correct, float)

    def fit(rr, cc):
        nll = lambda P: -np.sum(cc * np.log(1e-9 + 1 / (1 + 10 ** ((rr - P) / 400)))
                                + (1 - cc) * np.log(1e-9 + 1 - 1 / (1 + 10 ** ((rr - P) / 400))))
        return minimize_scalar(nll, bounds=(-500, 3500), method="bounded").x

    est = fit(r, c)
    rng = np.random.default_rng(seed)
    bs = [fit(r[i], c[i]) for i in rng.integers(0, len(r), (1000, len(r)))]
    return float(est), float(np.quantile(bs, .025)), float(np.quantile(bs, .975))
