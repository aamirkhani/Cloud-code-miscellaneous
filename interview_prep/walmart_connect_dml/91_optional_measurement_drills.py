"""
91 — OPTIONAL: Measurement / incrementality coding drills (reference solutions + self-tests).

Run:  python3 91_optional_measurement_drills.py      (numpy only)

Background for measuring creative performance (creative A/B tests, lift): experiment analysis, attribution,
privacy, streaming joins. Practice: implement each from the docstring in ~10-15 min and
talk through assumptions (estimand, variance, edge cases) as you go.
"""
import math
from collections import defaultdict, deque

import numpy as np

Z975, Z80 = 1.959963984540054, 0.8416212335729143


# ---------------------------------------------------------------------------
# 1. Sample size per arm for a difference in means
# ---------------------------------------------------------------------------
def sample_size_per_arm(sigma, mde, alpha_z=Z975, power_z=Z80):
    """n = 2 (z_{1-a/2} + z_{1-b})^2 sigma^2 / delta^2."""
    return math.ceil(2 * (alpha_z + power_z) ** 2 * sigma**2 / mde**2)


# ---------------------------------------------------------------------------
# 2. Difference in means with CI, and CUPED-adjusted version
# ---------------------------------------------------------------------------
def diff_in_means(y_t, y_c):
    y_t, y_c = np.asarray(y_t, float), np.asarray(y_c, float)
    d = y_t.mean() - y_c.mean()
    se = math.sqrt(y_t.var(ddof=1) / len(y_t) + y_c.var(ddof=1) / len(y_c))
    return d, se, (d - Z975 * se, d + Z975 * se)


def cuped_lift(y_t, x_t, y_c, x_c):
    """theta estimated on pooled data; adjust both arms around pooled pre-period mean."""
    y = np.r_[y_t, y_c]
    x = np.r_[x_t, x_c]
    theta = np.cov(x, y)[0, 1] / np.var(x, ddof=1)
    mx = x.mean()
    return diff_in_means(np.asarray(y_t) - theta * (np.asarray(x_t) - mx),
                         np.asarray(y_c) - theta * (np.asarray(x_c) - mx))


# ---------------------------------------------------------------------------
# 3. ITT, Wald/CACE, and ghost-ads ATT
# ---------------------------------------------------------------------------
def itt_and_cace(y_t, exposed_t, y_c):
    """One-sided noncompliance (control never exposed): CACE = ITT / exposure rate."""
    itt = float(np.mean(y_t) - np.mean(y_c))
    return itt, itt / float(np.mean(exposed_t))


def ghost_ads_att(y_t, exposed_t, y_c, ghost_exposed_c):
    """ATT = E[Y | treat, exposed] - E[Y | control, would-have-been-exposed]."""
    y_t, y_c = np.asarray(y_t, float), np.asarray(y_c, float)
    e_t, g_c = np.asarray(exposed_t, bool), np.asarray(ghost_exposed_c, bool)
    return diff_in_means(y_t[e_t], y_c[g_c])


# ---------------------------------------------------------------------------
# 4. Delta-method SE for a ratio metric (e.g. iROAS = incremental sales / spend,
#    or revenue per click when clicks are random)
# ---------------------------------------------------------------------------
def ratio_mean_se(num, den):
    """SE of sum(num)/sum(den) over i.i.d. units via the delta method."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    n = len(num)
    mx, my = num.mean(), den.mean()
    r = mx / my
    vx, vy = num.var(ddof=1), den.var(ddof=1)
    cxy = np.cov(num, den)[0, 1]
    var_r = (vx - 2 * r * cxy + r**2 * vy) / (n * my**2)
    return r, math.sqrt(var_r)


# ---------------------------------------------------------------------------
# 5. Sample-ratio-mismatch check (chi-square, 1 dof)
# ---------------------------------------------------------------------------
def srm_pvalue(n_t, n_c, expected_t_share=0.5):
    n = n_t + n_c
    e_t, e_c = n * expected_t_share, n * (1 - expected_t_share)
    chi2 = (n_t - e_t) ** 2 / e_t + (n_c - e_c) ** 2 / e_c
    return math.erfc(math.sqrt(chi2 / 2))  # survival of chi2(1)


# ---------------------------------------------------------------------------
# 6. Benjamini-Hochberg FDR across many campaign lift tests
# ---------------------------------------------------------------------------
def benjamini_hochberg(pvals, q=0.05):
    p = np.asarray(pvals)
    order = np.argsort(p)
    m = len(p)
    thresh = q * (np.arange(1, m + 1) / m)
    passed = p[order] <= thresh
    k = np.max(np.where(passed)[0]) + 1 if passed.any() else 0
    reject = np.zeros(m, bool)
    reject[order[:k]] = True
    return reject


# ---------------------------------------------------------------------------
# 7. Last-click attribution with lookback window and brand halo
# ---------------------------------------------------------------------------
def last_click_attribution(clicks, orders, item_brand, window_s=14 * 86400):
    """
    clicks: list of (user, ts, ad_item); orders: list of (order_id, user, ts, item, sales)
    Returns {order_id: (credited_ad_item, match_type)} where match_type in {"sku","brand"};
    SKU matches win over brand matches; most recent qualifying click wins within type.
    """
    by_user = defaultdict(list)
    for u, ts, item in clicks:
        by_user[u].append((ts, item))
    for u in by_user:
        by_user[u].sort()
    out = {}
    for oid, u, ts, item, _ in orders:
        best = {"sku": None, "brand": None}
        for cts, citem in by_user.get(u, []):
            if cts > ts:
                break
            if ts - cts > window_s:
                continue
            if citem == item:
                best["sku"] = citem
            elif item_brand.get(citem) == item_brand.get(item):
                best["brand"] = citem
        if best["sku"] is not None:
            out[oid] = (best["sku"], "sku")
        elif best["brand"] is not None:
            out[oid] = (best["brand"], "brand")
    return out


# ---------------------------------------------------------------------------
# 8. Synthetic control: simplex-constrained least squares via exponentiated gradient
# ---------------------------------------------------------------------------
def _project_simplex(v):
    """Euclidean projection onto {w >= 0, sum w = 1} (Duchi et al. 2008)."""
    u = np.sort(v)[::-1]
    css = np.cumsum(u)
    rho = np.nonzero(u * np.arange(1, len(v) + 1) > (css - 1))[0][-1]
    theta = (css[rho] - 1) / (rho + 1.0)
    return np.maximum(v - theta, 0)


def synthetic_control_weights(treated_pre, controls_pre, iters=20000):
    """
    treated_pre: (T,) pre-period series of treated geo; controls_pre: (T, J).
    Minimize ||treated - controls @ w||^2 s.t. w >= 0, sum w = 1 (projected gradient).
    """
    X, y = np.asarray(controls_pre, float), np.asarray(treated_pre, float)
    L = 2 * np.linalg.eigvalsh(X.T @ X).max()  # Lipschitz constant of the gradient
    w = np.full(X.shape[1], 1.0 / X.shape[1])
    for _ in range(iters):
        w = _project_simplex(w - (2 * X.T @ (X @ w - y)) / L)
    return w


# ---------------------------------------------------------------------------
# 9. Clean-room style release: k-threshold + Laplace DP noise on counts
# ---------------------------------------------------------------------------
def private_counts(counts, epsilon, k_min=50, rng=None):
    """Suppress cells with true count < k_min; add Laplace(1/epsilon) noise (sensitivity 1)."""
    rng = rng or np.random.default_rng()
    out = {}
    for key, c in counts.items():
        if c < k_min:
            continue
        out[key] = max(0, round(c + rng.laplace(0, 1.0 / epsilon)))
    return out


# ---------------------------------------------------------------------------
# 10. Streaming interval join with watermark (click -> order within window)
# ---------------------------------------------------------------------------
class StreamingLastClick:
    """
    Events arrive roughly in event-time order with bounded lateness.
    Keeps per-user click state with TTL = window; emits attribution on each order.
    Orders older than the watermark (max_event_ts - allowed_lateness) go to `late`
    for batch correction instead of being processed incorrectly.
    """

    def __init__(self, window_s, allowed_lateness_s):
        self.window = window_s
        self.lateness = allowed_lateness_s
        self.state = defaultdict(deque)  # user -> deque[(ts, item)] sorted by ts
        self.max_ts = -math.inf
        self.late = []

    @property
    def watermark(self):
        return self.max_ts - self.lateness

    def _evict(self, user):
        dq = self.state[user]
        while dq and dq[0][0] < self.watermark - self.window:
            dq.popleft()

    def on_click(self, user, ts, item):
        self.max_ts = max(self.max_ts, ts)
        dq = self.state[user]
        dq.append((ts, item))
        if len(dq) > 1 and dq[-2][0] > ts:  # keep sorted if slightly out of order
            items = sorted(dq)
            dq.clear()
            dq.extend(items)
        self._evict(user)

    def on_order(self, order_id, user, ts, item):
        if ts < self.watermark:
            self.late.append(order_id)
            return None
        self.max_ts = max(self.max_ts, ts)
        self._evict(user)  # lazy per-key TTL eviction (Flink would use state TTL / timers)
        hit = None
        for cts, citem in self.state.get(user, ()):
            if cts <= ts and ts - cts <= self.window and citem == item:
                hit = citem
        return hit


# ===========================================================================
# Self-tests (simulations with known ground truth)
# ===========================================================================
def _simulate_experiment(rng, n, true_effect, exposure_rate):
    """Users with pre-period spend x; would-be-exposed flag; effect only on exposed."""
    x = rng.gamma(1.2, 20.0, n)                     # pre-period category spend
    would_expose = rng.random(n) < exposure_rate     # same propensity in both arms
    treat = rng.random(n) < 0.5
    base = 0.6 * x + rng.gamma(1.0, 8.0, n)          # heavy-ish tail
    y = base + true_effect * (treat & would_expose)
    return x, would_expose, treat, y


def _tests():
    rng = np.random.default_rng(7)

    # 1. sample size matches 15.7 sigma^2 / delta^2
    assert sample_size_per_arm(10, 1) == math.ceil(15.6978 * 100) or abs(sample_size_per_arm(10, 1) - 1570) <= 1

    # 3. ITT vs CACE vs ghost ads: all recover truth, ghost ads with smaller SE than ITT-scaled
    x, we, t, y = _simulate_experiment(rng, 400_000, true_effect=2.0, exposure_rate=0.2)
    itt, cace = itt_and_cace(y[t], we[t], y[~t])
    assert abs(itt - 0.4) < 0.15, itt          # 2.0 * 0.2
    assert abs(cace - 2.0) < 0.75, cace
    att, se_att, _ = ghost_ads_att(y[t], we[t], y[~t], we[~t])
    assert abs(att - 2.0) < 4 * se_att, (att, se_att)
    _, se_itt, _ = diff_in_means(y[t], y[~t])
    assert se_att < se_itt / 0.2, "ghost ads must beat ITT/exposure-rate precision"

    # 2. CUPED: same estimate (unbiased), much smaller SE
    d_raw, se_raw, _ = diff_in_means(y[t], y[~t])
    d_cu, se_cu, _ = cuped_lift(y[t], x[t], y[~t], x[~t])
    assert se_cu < 0.7 * se_raw, (se_cu, se_raw)
    assert abs(d_cu - 0.4) < 4 * se_cu

    # 4. Delta method SE agrees with bootstrap
    num = rng.gamma(2, 5, 5000)
    den = num * 0.2 + rng.gamma(2, 1, 5000)
    r, se = ratio_mean_se(num, den)
    boots = []
    for _ in range(400):
        idx = rng.integers(0, 5000, 5000)
        boots.append(num[idx].sum() / den[idx].sum())
    assert abs(se - np.std(boots)) / np.std(boots) < 0.15

    # 5. SRM
    assert srm_pvalue(50_000, 50_100) > 0.05
    assert srm_pvalue(50_000, 51_500) < 1e-3

    # 6. BH
    rej = benjamini_hochberg([0.001, 0.008, 0.039, 0.041, 0.042, 0.06, 0.074, 0.205, 0.212, 0.216])
    assert rej.tolist() == [True, True] + [False] * 8

    # 7. Attribution
    brand = {"tide_pods": "tide", "tide_liquid": "tide", "gain": "gain"}
    clicks = [("u1", 0, "tide_liquid"), ("u1", 100, "gain"), ("u1", 200, "tide_pods"),
              ("u2", 0, "tide_pods")]
    orders = [("o1", "u1", 300, "tide_pods", 12.0),          # sku match (latest)
              ("o2", "u1", 300, "tide_liquid", 15.0),        # sku match at t=0 beats brand
              ("o3", "u2", 15 * 86400, "tide_pods", 12.0),   # outside 14d window
              ("o4", "u1", 400, "tide_liquid", 15.0)]
    a = last_click_attribution(clicks, orders, brand)
    assert a["o1"] == ("tide_pods", "sku") and a["o2"] == ("tide_liquid", "sku")
    assert "o3" not in a
    clicks2 = [("u3", 0, "tide_pods")]
    a2 = last_click_attribution(clicks2, [("o5", "u3", 10, "tide_liquid", 9.0)], brand)
    assert a2["o5"] == ("tide_pods", "brand")

    # 8. Synthetic control recovers weights and the post-period effect
    T_pre, T_post, J = 60, 20, 6
    base = 100 + rng.normal(0, 2, (T_pre + T_post, J)).cumsum(axis=0)  # independent random walks
    true_w = np.array([0.5, 0.3, 0.2, 0, 0, 0])
    treated = base @ true_w + rng.normal(0, 0.2, T_pre + T_post)
    treated[T_pre:] += 5.0  # campaign effect
    w = synthetic_control_weights(treated[:T_pre], base[:T_pre])
    effect = np.mean(treated[T_pre:] - base[T_pre:] @ w)
    assert abs(effect - 5.0) < 1.0, (effect, w.round(2))

    # 9. Private counts: small cells suppressed, large cells close to truth
    pc = private_counts({"seg_a": 10_000, "seg_b": 20}, epsilon=1.0, rng=rng)
    assert "seg_b" not in pc and abs(pc["seg_a"] - 10_000) < 20

    # 10. Streaming join
    s = StreamingLastClick(window_s=3600, allowed_lateness_s=60)
    s.on_click("u", 0, "milk")
    s.on_click("v", 10, "eggs")
    assert s.on_order("o1", "u", 1800, "milk") == "milk"
    assert s.on_order("o2", "u", 5000, "milk") is None       # outside window
    s.on_click("w", 10_000, "bread")                          # advances watermark
    assert s.on_order("o3", "v", 100, "eggs") is None and "o3" in s.late
    assert s.on_order("o4", "u", 10_050, "milk") is None
    assert len(s.state["u"]) == 0                              # evicted by TTL

    print("All 10 measurement drills pass.")


if __name__ == "__main__":
    _tests()
