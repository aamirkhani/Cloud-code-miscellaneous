"""
08 — Ads-flavored ML coding drills (with reference solutions + self-tests).

Run:  python3 08_coding_drills.py        (needs only numpy)

How to practice: read the docstring, close this file, implement it yourself in a blank
file in ~10-15 min, then compare. Talk while you code: state complexity and edge cases.
Distinguished-level coding rounds care about clarity, correctness and tradeoffs more
than tricks.
"""
import heapq
import math
import random
from collections import defaultdict

import numpy as np


# ---------------------------------------------------------------------------
# 1. AUC from scratch (rank-based / Mann-Whitney U), handles ties. O(n log n)
# ---------------------------------------------------------------------------
def auc(y_true, y_score):
    """Probability a random positive is scored above a random negative (ties = 0.5)."""
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    n_pos = int(y_true.sum())
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        raise ValueError("AUC undefined with one class")
    order = np.argsort(y_score, kind="mergesort")
    s = y_score[order]
    ranks = np.empty(len(s))
    i = 0
    while i < len(s):  # average ranks over ties
        j = i
        while j + 1 < len(s) and s[j + 1] == s[i]:
            j += 1
        ranks[i : j + 1] = (i + j) / 2.0 + 1
        i = j + 1
    pos_rank_sum = ranks[y_true[order] == 1].sum()
    return (pos_rank_sum - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)


# ---------------------------------------------------------------------------
# 2. GAUC: impression-weighted per-group AUC (groups = user or query)
# ---------------------------------------------------------------------------
def gauc(groups, y_true, y_score):
    by = defaultdict(lambda: ([], []))
    for g, y, s in zip(groups, y_true, y_score):
        by[g][0].append(y)
        by[g][1].append(s)
    num = den = 0.0
    for ys, ss in by.values():
        if 0 < sum(ys) < len(ys):  # skip single-class groups
            num += len(ys) * auc(ys, ss)
            den += len(ys)
    return num / den


# ---------------------------------------------------------------------------
# 3. Log loss and Normalized Entropy (NE = logloss / entropy of base rate)
# ---------------------------------------------------------------------------
def log_loss(y, p, eps=1e-12):
    y = np.asarray(y, float)
    p = np.clip(np.asarray(p, float), eps, 1 - eps)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def normalized_entropy(y, p):
    ctr = float(np.mean(y))
    base = -(ctr * math.log(ctr) + (1 - ctr) * math.log(1 - ctr))
    return log_loss(y, p) / base  # < 1 means better than predicting the base rate


# ---------------------------------------------------------------------------
# 4. Calibration: downsampling correction, calibration ratio, ECE, isotonic (PAV)
# ---------------------------------------------------------------------------
def correct_downsampling(p_prime, neg_keep_rate):
    """Model trained with negatives kept at rate w -> true probability."""
    p_prime = np.asarray(p_prime, float)
    return p_prime / (p_prime + (1 - p_prime) / neg_keep_rate)


def calibration_ratio(y, p):
    return float(np.sum(p) / np.sum(y))  # target 1.0


def ece(y, p, n_bins=10):
    y, p = np.asarray(y, float), np.asarray(p, float)
    bins = np.minimum((p * n_bins).astype(int), n_bins - 1)
    total = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            total += m.mean() * abs(y[m].mean() - p[m].mean())
    return total


def isotonic_fit(scores, y):
    """Pool-Adjacent-Violators. Returns (sorted_scores, fitted_values) for step lookup."""
    order = np.argsort(scores)
    xs = np.asarray(scores, float)[order]
    blocks = []  # each: [sum_y, count, max_x]
    for x, t in zip(xs, np.asarray(y, float)[order]):
        blocks.append([t, 1, x])
        while len(blocks) > 1 and blocks[-2][0] / blocks[-2][1] > blocks[-1][0] / blocks[-1][1]:
            s, c, mx = blocks.pop()
            blocks[-1][0] += s
            blocks[-1][1] += c
            blocks[-1][2] = mx
    thresholds = np.array([b[2] for b in blocks])
    values = np.array([b[0] / b[1] for b in blocks])
    return thresholds, values


def isotonic_predict(thresholds, values, s):
    idx = np.searchsorted(thresholds, s, side="left")
    return values[np.minimum(idx, len(values) - 1)]


# ---------------------------------------------------------------------------
# 5. GSP auction with reserve price and relevance floor
# ---------------------------------------------------------------------------
def gsp_auction(ads, n_slots, reserve_cpc=0.05, relevance_floor=0.3):
    """
    ads: list of dicts {id, bid, pctr, relevance}
    Rank by bid*pctr among eligible ads. Price for slot i = max(reserve,
    score_{i+1}/pctr_i), never above own bid. Returns [(id, cpc_price)].
    """
    eligible = [a for a in ads if a["relevance"] >= relevance_floor and a["bid"] >= reserve_cpc]
    eligible.sort(key=lambda a: a["bid"] * a["pctr"], reverse=True)
    winners = eligible[:n_slots]
    out = []
    for i, a in enumerate(winners):
        if i + 1 < len(eligible):
            nxt = eligible[i + 1]
            price = nxt["bid"] * nxt["pctr"] / a["pctr"]
        else:
            price = reserve_cpc
        out.append((a["id"], round(min(a["bid"], max(reserve_cpc, price)) + 1e-12, 4)))
    return out


# ---------------------------------------------------------------------------
# 6. Budget pacing via online dual gradient descent (bid = value / lambda)
# ---------------------------------------------------------------------------
def simulate_pacing(budget, values, market_prices, traffic_curve, eta=0.5, lam0=1.0):
    """
    Second-price setting: we win auction t iff bid >= market_price[t], and pay market_price.
    traffic_curve: expected fraction of the day's opportunities at each step (sums to 1);
    target spend at step t = budget * cumulative traffic share.
    Returns (total_spend, total_value, lambda_trace).
    """
    lam, spend, value = lam0, 0.0, 0.0
    target_cum = np.cumsum(traffic_curve) * budget
    trace = []
    for t, (v, mp) in enumerate(zip(values, market_prices)):
        bid = v / lam
        if bid >= mp and spend + mp <= budget:
            spend += mp
            value += v
        # Raise lambda (bid lower) when ahead of plan, lower it when behind.
        err = (spend - target_cum[t]) / budget
        lam = max(1e-3, lam * math.exp(eta * err))  # multiplicative update keeps lambda > 0
        trace.append(lam)
    return spend, value, trace


# ---------------------------------------------------------------------------
# 7. Logistic regression with hashed features + FTRL-style simplicity (plain SGD + L2)
# ---------------------------------------------------------------------------
class HashedLR:
    def __init__(self, dim=2**18, lr=0.1, l2=1e-6):
        self.w = np.zeros(dim)
        self.dim, self.lr, self.l2 = dim, lr, l2

    def _idx(self, feats):  # feats like ["user=123", "query=tv", "user=123_x_cat=tv"]
        return [hash(f) % self.dim for f in feats]

    def predict(self, feats):
        z = sum(self.w[i] for i in self._idx(feats))
        return 1 / (1 + math.exp(-max(min(z, 35), -35)))

    def update(self, feats, y):
        p = self.predict(feats)
        g = p - y  # d(logloss)/dz
        for i in self._idx(feats):
            self.w[i] -= self.lr * (g + self.l2 * self.w[i])
        return p


# ---------------------------------------------------------------------------
# 8. Bayesian-smoothed CTR (Beta prior) for cold start
# ---------------------------------------------------------------------------
def smoothed_ctr(clicks, imps, prior_ctr, prior_strength=100):
    """Posterior mean with Beta(alpha=prior_ctr*k, beta=(1-prior_ctr)*k)."""
    a = prior_ctr * prior_strength
    b = (1 - prior_ctr) * prior_strength
    return (clicks + a) / (imps + a + b)


# ---------------------------------------------------------------------------
# 9. Thompson sampling for creative selection
# ---------------------------------------------------------------------------
def thompson_select(stats, rng):
    """stats: {creative_id: (clicks, imps)} -> chosen creative id."""
    best, best_s = None, -1
    for cid, (c, n) in stats.items():
        s = rng.betavariate(1 + c, 1 + n - c)
        if s > best_s:
            best, best_s = cid, s
    return best


# ---------------------------------------------------------------------------
# 10. InfoNCE with in-batch negatives + logQ (popularity) correction, numpy
# ---------------------------------------------------------------------------
def infonce_logq(q, a, item_logq, tau=0.05):
    """
    q, a: (B, d) L2-normalized query/item embeddings; row i of a is the positive for q[i].
    item_logq: (B,) log sampling probability of each in-batch item.
    Returns mean loss.
    """
    logits = (q @ a.T) / tau - item_logq[None, :]
    logits -= logits.max(axis=1, keepdims=True)
    log_softmax = logits - np.log(np.exp(logits).sum(axis=1, keepdims=True))
    return float(-np.mean(np.diag(log_softmax)))


# ---------------------------------------------------------------------------
# 11. CUPED variance reduction
# ---------------------------------------------------------------------------
def cuped(y, x_pre):
    y, x_pre = np.asarray(y, float), np.asarray(x_pre, float)
    theta = np.cov(x_pre, y)[0, 1] / np.var(x_pre, ddof=1)
    return y - theta * (x_pre - x_pre.mean())


# ---------------------------------------------------------------------------
# 12. Streaming utilities: top-K advertisers by spend, reservoir sampling of impressions
# ---------------------------------------------------------------------------
def top_k_spenders(stream, k):
    """stream of (advertiser, amount) -> top k by total. O(n + m log k)."""
    totals = defaultdict(float)
    for adv, amt in stream:
        totals[adv] += amt
    return heapq.nlargest(k, totals.items(), key=lambda kv: kv[1])


def reservoir_sample(stream, k, rng):
    res = []
    for i, x in enumerate(stream):
        if i < k:
            res.append(x)
        else:
            j = rng.randint(0, i)
            if j < k:
                res[j] = x
    return res


# ---------------------------------------------------------------------------
# 13. Shapley-value multi-touch attribution (exact, small number of channels)
# ---------------------------------------------------------------------------
def shapley_attribution(channels, conv_rate):
    """conv_rate: function(frozenset_of_channels) -> conversion rate. Exact Shapley."""
    from itertools import combinations

    n = len(channels)
    phi = {c: 0.0 for c in channels}
    for c in channels:
        others = [o for o in channels if o != c]
        for r in range(len(others) + 1):
            for S in combinations(others, r):
                S = frozenset(S)
                w = math.factorial(len(S)) * math.factorial(n - len(S) - 1) / math.factorial(n)
                phi[c] += w * (conv_rate(S | {c}) - conv_rate(S))
    return phi


# ===========================================================================
# Self-tests
# ===========================================================================
def _tests():
    rng_np = np.random.default_rng(0)
    rng = random.Random(0)

    # AUC
    assert abs(auc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]) - 0.75) < 1e-9
    assert abs(auc([0, 1], [0.5, 0.5]) - 0.5) < 1e-9
    y = rng_np.integers(0, 2, 2000)
    s = y * 0.3 + rng_np.random(2000)
    pairs = [(a, b) for a in s[y == 1][:200] for b in s[y == 0][:200]]
    brute = np.mean([1.0 if a > b else 0.5 if a == b else 0.0 for a, b in pairs])
    assert abs(auc(np.r_[np.ones(200), np.zeros(200)], np.r_[s[y == 1][:200], s[y == 0][:200]]) - brute) < 1e-9

    # GAUC
    g = gauc(["u1"] * 4 + ["u2"] * 2, [0, 1, 0, 1, 0, 1], [0.1, 0.9, 0.2, 0.8, 0.7, 0.3])
    assert abs(g - (4 * 1.0 + 2 * 0.0) / 6) < 1e-9

    # NE: perfect base-rate predictor -> NE = 1
    yy = rng_np.random(10000) < 0.03
    assert abs(normalized_entropy(yy, np.full(10000, yy.mean())) - 1.0) < 1e-9

    # Downsampling correction recovers true rate
    true_p = 0.02
    w = 0.1  # keep 10% negatives
    p_train = true_p / (true_p + (1 - true_p) * w)
    assert abs(correct_downsampling(p_train, w) - true_p) < 1e-12

    # Isotonic fixes a miscalibrated (over-predicting) model
    scores = rng_np.random(20000)
    labels = (rng_np.random(20000) < scores**2).astype(float)  # true p = s^2, model says s
    th, vals = isotonic_fit(scores, labels)
    calibrated = isotonic_predict(th, vals, scores)
    assert ece(labels, calibrated) < ece(labels, scores)
    assert abs(calibration_ratio(labels, calibrated) - 1.0) < 0.02

    # GSP worked example from 02_ads_ml_fundamentals.md
    ads = [
        {"id": "A", "bid": 1.00, "pctr": 0.05, "relevance": 0.9},
        {"id": "B", "bid": 2.00, "pctr": 0.02, "relevance": 0.8},
        {"id": "C", "bid": 0.50, "pctr": 0.06, "relevance": 0.7},
        {"id": "D", "bid": 9.00, "pctr": 0.10, "relevance": 0.1},  # irrelevant: filtered
    ]
    res = gsp_auction(ads, n_slots=2)
    assert [r[0] for r in res] == ["A", "B"]
    assert abs(res[0][1] - 0.80) < 1e-6 and abs(res[1][1] - 1.50) < 1e-6

    # Pacing: spends close to budget, not front-loaded
    T = 5000
    traffic = np.ones(T) / T
    values = rng_np.gamma(2.0, 0.5, T)
    prices = rng_np.gamma(2.0, 0.5, T)
    spend, val, trace = simulate_pacing(budget=300.0, values=values, market_prices=prices, traffic_curve=traffic)
    assert 0.9 * 300 <= spend <= 300.0, spend
    # Value per dollar should beat a greedy "bid = value until broke" baseline
    g_spend = g_val = 0.0
    for v, mp in zip(values, prices):
        if v >= mp and g_spend + mp <= 300:
            g_spend += mp
            g_val += v
    assert val > g_val, (val, g_val)

    # Hashed LR learns a simple pattern
    m = HashedLR(dim=2**12, lr=0.2)
    for _ in range(3000):
        q = rng.choice(["tv", "milk"])
        cat = rng.choice(["electronics", "grocery"])
        match = (q == "tv") == (cat == "electronics")
        yv = 1 if rng.random() < (0.3 if match else 0.02) else 0
        m.update([f"q={q}", f"cat={cat}", f"q={q}_x_cat={cat}"], yv)
    assert m.predict(["q=tv", "cat=electronics", "q=tv_x_cat=electronics"]) > m.predict(
        ["q=tv", "cat=grocery", "q=tv_x_cat=grocery"]
    )

    # Smoothing: new ad with 1 click / 2 imps is pulled toward prior
    assert abs(smoothed_ctr(1, 2, 0.02) - (1 + 2) / (2 + 100)) < 1e-12

    # Thompson converges to best creative
    true = {"c1": 0.02, "c2": 0.05, "c3": 0.03}
    st = {k: (0, 0) for k in true}
    for _ in range(20000):
        k = thompson_select(st, rng)
        c, n = st[k]
        st[k] = (c + (rng.random() < true[k]), n + 1)
    assert max(st, key=lambda k: st[k][1]) == "c2"

    # InfoNCE: aligned embeddings -> lower loss than random
    B, d = 64, 16
    qv = rng_np.normal(size=(B, d))
    qv /= np.linalg.norm(qv, axis=1, keepdims=True)
    av = qv + 0.05 * rng_np.normal(size=(B, d))
    av /= np.linalg.norm(av, axis=1, keepdims=True)
    rv = rng_np.normal(size=(B, d))
    rv /= np.linalg.norm(rv, axis=1, keepdims=True)
    lq = np.log(np.full(B, 1.0 / B))
    assert infonce_logq(qv, av, lq) < infonce_logq(qv, rv, lq)

    # CUPED reduces variance, preserves mean
    x = rng_np.normal(100, 20, 5000)
    yv = 0.8 * x + rng_np.normal(0, 5, 5000)
    adj = cuped(yv, x)
    assert np.var(adj) < 0.2 * np.var(yv) and abs(adj.mean() - yv.mean()) < 1e-9

    # Top-K / reservoir
    assert top_k_spenders([("a", 5), ("b", 3), ("a", 1), ("c", 10)], 2) == [("c", 10), ("a", 6)]
    counts = defaultdict(int)
    for _ in range(4000):
        for x_ in reservoir_sample(range(10), 3, rng):
            counts[x_] += 1
    assert all(abs(c / 4000 - 0.3) < 0.05 for c in counts.values())

    # Shapley: additive game -> each channel gets its own contribution
    base = {"search": 0.03, "display": 0.01, "ctv": 0.005}
    phi = shapley_attribution(list(base), lambda S: sum(base[c] for c in S))
    assert all(abs(phi[c] - base[c]) < 1e-12 for c in base)

    print("All 13 drills pass.")


if __name__ == "__main__":
    _tests()
