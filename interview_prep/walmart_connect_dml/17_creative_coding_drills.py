"""
17 — Creative Intelligence coding drills (reference solutions + self-tests).

Run:  python3 -I 17_creative_coding_drills.py        (numpy + standard library only)

Role lens: Walmart Ads Distinguished Data Scientist, Creative Intelligence. That means
generative ad creative (images / copy / video), automated evaluation with a
model-as-judge calibrated against human and advertiser preference, drift detection,
artifact / product-fidelity checks, structured creative attributes, composition and
adaptation across placements (cropping, text placement), and WCAG 2.2 AA accessibility.

How to practice:
  1. Read one drill's docstring (that is the interviewer's prompt). Close this file.
  2. In a blank file, implement it in ~10-15 minutes, talking out loud: restate the
     problem, give the brute force, then the better algorithm, its complexity, and
     the edge cases (ties, empty input, degenerate shapes, class imbalance).
  3. Compare with the reference here, then run this file to check yourself.
  4. For each drill, have a one-line answer to "how would this run in production at
     Walmart scale?" (vectorize, batch, approximate, monitor). The comments under
     each solution give one.
Distinguished-level coding rounds reward clarity, correctness and judgment about
tradeoffs more than tricks. Say what you would measure, not only what you would code.

Drills
   1  Bradley-Terry (MM) from pairwise preferences + Elo as the streaming alternative
   2  Judge-vs-human agreement: percent agreement, Cohen's kappa, quadratic weighted
      kappa, Spearman with average-rank ties
   3  Judge calibration: isotonic (PAV), ECE, auto-approve threshold at target precision
   4  Position bias in a pairwise LLM judge: estimate, swap-average, flag inconsistency
   5  Drift: Population Stability Index + two-sample KS from scratch + alert rule
   6  CUSUM change detection on a daily approval-rate stream
   7  WCAG 2.2 contrast: luminance, ratio, AA pass/fail, text-color pick, scrim alpha
   8  Saliency-aware smart crop with a summed-area table
   9  Headline placement: largest low-clutter rectangle (histogram-stack)
  10  Product fidelity: SSIM from scratch + aHash / dHash Hamming distance
  11  Brand palette adherence: sRGB -> CIELAB, Delta E 76/94, seeded k-means
  12  Layout rule validator: IoU, safe zone, logo size, text/product overlap, target size
  13  Thompson sampling (Beta) + top-two Thompson for best-variant identification
  14  Near-duplicate creative dedupe: cosine similarity + union-find
"""
import math
from collections import defaultdict

import numpy as np


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


# ---------------------------------------------------------------------------
# 1. Bradley-Terry from pairwise preferences (MM algorithm) + Elo streaming update
# ---------------------------------------------------------------------------
def bradley_terry_mm(wins, prior=0.1, n_iter=1000, tol=1e-10):
    """
    Prompt: raters (or a judge model) saw pairs of creative variants and picked the
    better one. wins[i, j] = number of times variant i was preferred over variant j.
    Fit a Bradley-Terry model, P(i beats j) = p_i / (p_i + p_j), and return the latent
    log-quality theta_i = log p_i (centered to mean 0) so we can rank the variants.

    Method: Hunter's (2004) minorize-maximize update
        p_i <- W_i / sum_j n_ij / (p_i + p_j)
    where W_i is i's total wins and n_ij = wins[i, j] + wins[j, i]. Each step raises
    the likelihood, with no step size to tune. `prior` adds that many virtual wins in
    each direction for every pair. This smooths the estimates, and it also makes the
    comparison graph strongly connected, which the MLE needs in order to exist (an
    item that never wins would otherwise go to -inf).
    """
    W = np.asarray(wins, float).copy()
    n = W.shape[0]
    W += prior * (1 - np.eye(n))
    N = W + W.T  # comparisons per pair
    w = W.sum(axis=1)  # total wins per item
    p = np.ones(n)
    for _ in range(n_iter):
        denom = (N / (p[:, None] + p[None, :])).sum(axis=1)
        p_new = w / denom
        p_new /= np.exp(np.mean(np.log(p_new)))  # fix the scale (BT is scale-free)
        done = np.max(np.abs(np.log(p_new) - np.log(p))) < tol
        p = p_new
        if done:
            break
    theta = np.log(p)
    return theta - theta.mean()
    # Complexity: O(n^2) per iteration, where n = number of variants. For a sparse
    # comparison graph, loop over the observed pairs instead: O(#pairs) per iteration.


def elo_update(r_a, r_b, score_a, k=16.0):
    """One Elo step. score_a is 1 if A won, 0 if B won, 0.5 for a tie."""
    e_a = 1.0 / (1.0 + 10 ** ((r_b - r_a) / 400.0))
    delta = k * (score_a - e_a)
    return r_a + delta, r_b - delta


def elo_stream(n_items, matches, k=16.0, init=1500.0):
    """
    Prompt follow-up: judgments arrive as a stream and we cannot refit BT every time.
    Elo is online SGD on the same logistic model (theta = rating * ln10 / 400). It is
    O(1) per match, but its result depends on the order of matches and it is noisier
    than a batch fit. In practice: Elo for live leaderboards, periodic BT refits for
    reporting.
    """
    r = np.full(n_items, init, dtype=float)
    for a, b, s in matches:
        r[a], r[b] = elo_update(r[a], r[b], s, k)
    return r


# ---------------------------------------------------------------------------
# 2. Agreement between judge and humans: % agreement, Cohen's kappa, QWK, Spearman
# ---------------------------------------------------------------------------
def percent_agreement(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return float(np.mean(a == b))


def cohen_kappa(a, b):
    """
    Prompt: a judge model and a human rater labeled the same creatives (for example
    approve / reject). Percent agreement looks high when one class dominates, so report
    a chance-corrected agreement as well:
        kappa = (p_o - p_e) / (1 - p_e)
    where p_o is observed agreement and p_e = sum_k P_a(k) P_b(k) is the agreement
    expected if both raters labeled independently at their own base rates.
    """
    a, b = np.asarray(a), np.asarray(b)
    labels = np.unique(np.concatenate([a, b]))
    po = np.mean(a == b)
    pe = sum(np.mean(a == k) * np.mean(b == k) for k in labels)
    if pe == 1.0:  # both raters used one identical label throughout
        return 1.0
    return float((po - pe) / (1 - pe))
    # O(n * K) for K labels.


def quadratic_weighted_kappa(a, b, n_classes):
    """
    Kappa for ordinal ratings (such as 1-5 quality scores) where a near-miss counts
    as partial agreement: kappa_w = 1 - sum(w * O) / sum(w * E), with
    w_ij = (i - j)^2 / (K - 1)^2. Labels are integers in [0, n_classes).
    """
    a, b = np.asarray(a, int), np.asarray(b, int)
    K = n_classes
    O = np.zeros((K, K))
    np.add.at(O, (a, b), 1)
    E = np.outer(O.sum(1), O.sum(0)) / O.sum()
    i, j = np.indices((K, K))
    w = (i - j) ** 2 / (K - 1) ** 2
    denom = (w * E).sum()
    return 1.0 if denom == 0 else float(1 - (w * O).sum() / denom)


def rankdata_avg(x):
    """1-based ranks; tied values get the average of the ranks they span. O(n log n)."""
    x = np.asarray(x, float)
    order = np.argsort(x, kind="mergesort")
    xs = x[order]
    ranks = np.empty(len(x))
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1
        i = j + 1
    return ranks


def spearman(x, y):
    """
    Prompt: does the judge order creatives the way humans do? Spearman rho is the
    Pearson correlation of the ranks. With ties, use average ranks and Pearson on
    them. The shortcut 1 - 6 sum d^2 / (n(n^2-1)) is only exact when there are no ties.
    """
    rx, ry = rankdata_avg(x), rankdata_avg(y)
    rx -= rx.mean()
    ry -= ry.mean()
    denom = math.sqrt((rx @ rx) * (ry @ ry))
    return float(rx @ ry / denom) if denom > 0 else 0.0


# ---------------------------------------------------------------------------
# 3. Judge calibration: isotonic (PAV) -> P(human approves); ECE; precision threshold
# ---------------------------------------------------------------------------
def pav_fit(scores, y):
    """
    Prompt: the judge outputs a raw score in [0, 1], but 0.8 does not mean an 80%
    chance that a human approves. Fit a monotone map from raw score to
    P(approve | score) using Pool-Adjacent-Violators.
    Returns (block_upper_x, block_value), a step function. O(n log n) for the sort,
    then O(n) amortized for the merges.
    """
    order = np.argsort(scores, kind="mergesort")
    xs = np.asarray(scores, float)[order]
    ys = np.asarray(y, float)[order]
    sums, cnts, xmax = [], [], []
    for x, t in zip(xs, ys):
        sums.append(t)
        cnts.append(1)
        xmax.append(x)
        while len(sums) > 1 and sums[-2] / cnts[-2] > sums[-1] / cnts[-1]:
            s, c, m = sums.pop(), cnts.pop(), xmax.pop()
            sums[-1] += s
            cnts[-1] += c
            xmax[-1] = m
    return np.array(xmax), np.array(sums) / np.array(cnts)


def pav_predict(block_x, block_v, s):
    idx = np.searchsorted(block_x, np.asarray(s, float), side="left")
    return block_v[np.minimum(idx, len(block_v) - 1)]


def ece(y, p, n_bins=10):
    """Expected calibration error with equal-width bins: sum_b (n_b/n) |mean y - mean p|."""
    y, p = np.asarray(y, float), np.asarray(p, float)
    bins = np.minimum((p * n_bins).astype(int), n_bins - 1)
    total = 0.0
    for b in range(n_bins):
        m = bins == b
        if m.any():
            total += m.mean() * abs(y[m].mean() - p[m].mean())
    return float(total)


def wilson_lower(k, n, z=1.645):
    """One-sided ~95% Wilson lower confidence bound on a binomial proportion."""
    if n == 0:
        return 0.0
    ph = k / n
    centre = ph + z * z / (2 * n)
    margin = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return (centre - margin) / (1 + z * z / n)


def auto_approve_threshold(scores, y, target_precision=0.95, conservative=True, min_support=50):
    """
    Prompt: route generated creatives. If score >= t, auto-approve; otherwise send to
    human review. Pick the t that maximizes recall (the share of good creatives that
    skip review) subject to precision on the auto-approved set >= target_precision.
    Report the threshold, precision, recall and coverage (share auto-approved).

    Sort by score descending. Precision of the top-k set is not monotone in k, so
    scan every cut and keep the largest k that meets the target. Only cut between
    distinct score values, because ties cannot be split. With conservative=True the
    precision test uses the Wilson lower bound, which guards against the optimism of
    picking a threshold in-sample. Still confirm the result on a held-out set.
    O(n log n).
    """
    s = np.asarray(scores, float)
    y = np.asarray(y, float)
    order = np.argsort(-s, kind="mergesort")
    ss, yy = s[order], y[order]
    tp = np.cumsum(yy)
    total_pos = yy.sum()
    best = None
    for k in range(min_support, len(ss) + 1):
        if k < len(ss) and ss[k] == ss[k - 1]:
            continue  # not a valid cut: would split a tie
        prec = tp[k - 1] / k
        ok = wilson_lower(tp[k - 1], k) if conservative else prec
        if ok >= target_precision:
            best = (k, prec)
    if best is None:
        return {"threshold": math.inf, "precision": float("nan"), "recall": 0.0, "coverage": 0.0}
    k, prec = best
    return {
        "threshold": float(ss[k - 1]),
        "precision": float(prec),
        "recall": float(tp[k - 1] / total_pos),
        "coverage": k / len(ss),
    }
    # Production: refit per surface / category and per judge version; monitor realized
    # precision with a small random audit of auto-approved items (that audit is also
    # your unbiased label stream). Add a mirrored auto-reject threshold if useful.


# ---------------------------------------------------------------------------
# 4. Position bias in a pairwise LLM judge: estimate, debias by swapping, flag flips
# ---------------------------------------------------------------------------
def position_bias_report(p_ab, p_ba, margin=0.0, eps=1e-6):
    """
    Prompt: for each pair (a, b) the judge ran twice: once with a in slot 1, giving
    p_ab = P(slot 1 wins), and once with b in slot 1, giving p_ba = P(slot 1 wins).
    Inputs can be probabilities or 0/1 verdicts. Estimate the judge's position bias,
    return a debiased P(a > b), and flag the pairs whose verdict depends on the order.

    Model: logit p_ab = d + beta,  logit p_ba = -d + beta,  with d the true a-vs-b gap.
      beta_hat = mean(0.5 * (logit p_ab + logit p_ba))   (only meaningful for probabilities)
      first_slot_rate = mean of all slot-1 wins; under a balanced design the quality
      effects cancel, so first_slot_rate - 0.5 measures the bias directly.
      debiased P(a > b) = 0.5 * (p_ab + (1 - p_ba))   (swap-averaging)
      inconsistent: the same slot wins in both orders, i.e.
      (p_ab - 0.5) and (p_ba - 0.5) share a sign (beyond `margin`).
    O(n).
    """
    p_ab = np.asarray(p_ab, float)
    p_ba = np.asarray(p_ba, float)
    first_slot_rate = float(np.mean(np.concatenate([p_ab, p_ba])))
    la = np.log(np.clip(p_ab, eps, 1 - eps) / np.clip(1 - p_ab, eps, 1 - eps))
    lb = np.log(np.clip(p_ba, eps, 1 - eps) / np.clip(1 - p_ba, eps, 1 - eps))
    beta_logit = float(np.mean(0.5 * (la + lb)))
    debiased = 0.5 * (p_ab + 1 - p_ba)
    inconsistent = ((p_ab - 0.5) > margin) & ((p_ba - 0.5) > margin) | (
        (p_ab - 0.5) < -margin
    ) & ((p_ba - 0.5) < -margin)
    return {
        "first_slot_rate": first_slot_rate,
        "bias": first_slot_rate - 0.5,
        "beta_logit": beta_logit,
        "debiased_pref": debiased,
        "inconsistent": inconsistent,
        "consistency_rate": float(1 - inconsistent.mean()),
    }
    # Talking points: randomize order at eval time; treat inconsistent pairs as ties
    # or send them to humans; add a position term beta to a Bradley-Terry fit; and
    # track consistency_rate as a judge health metric across judge or prompt versions.


# ---------------------------------------------------------------------------
# 5. Drift: Population Stability Index + two-sample KS from scratch + alert rule
# ---------------------------------------------------------------------------
def psi(ref, cur, n_bins=10, eps=1e-4):
    """
    Prompt: has the distribution of judge scores (or of a creative attribute) moved
    between a reference window and the current window?
        PSI = sum_b (c_b - r_b) * ln(c_b / r_b)
    using bins at the reference quantiles. Rule of thumb: < 0.1 stable,
    0.1-0.25 moderate shift, > 0.25 major shift. O((n + m) log B).
    """
    ref, cur = np.asarray(ref, float), np.asarray(cur, float)
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, n_bins + 1))[1:-1])
    r = np.bincount(np.searchsorted(edges, ref, side="right"), minlength=len(edges) + 1) / len(ref)
    c = np.bincount(np.searchsorted(edges, cur, side="right"), minlength=len(edges) + 1) / len(cur)
    r, c = np.maximum(r, eps), np.maximum(c, eps)
    return float(np.sum((c - r) * np.log(c / r)))


def ks_2samp(a, b):
    """
    Two-sample Kolmogorov-Smirnov: D = sup_x |F_a(x) - F_b(x)|, evaluated at every
    pooled sample point, plus the asymptotic p-value
        Q(lam) = 2 sum_{k>=1} (-1)^{k-1} exp(-2 k^2 lam^2),
        lam = (sqrt(ne) + 0.12 + 0.11/sqrt(ne)) * D,  ne = n m / (n + m).
    O((n + m) log(n + m)).
    """
    a, b = np.sort(np.asarray(a, float)), np.sort(np.asarray(b, float))
    pooled = np.concatenate([a, b])
    fa = np.searchsorted(a, pooled, side="right") / len(a)
    fb = np.searchsorted(b, pooled, side="right") / len(b)
    D = float(np.max(np.abs(fa - fb)))
    ne = len(a) * len(b) / (len(a) + len(b))
    lam = (math.sqrt(ne) + 0.12 + 0.11 / math.sqrt(ne)) * D
    if lam < 1e-3:
        return D, 1.0
    k = np.arange(1, 101)
    p = 2 * np.sum((-1.0) ** (k - 1) * np.exp(-2 * k**2 * lam**2))
    return D, float(min(max(p, 0.0), 1.0))


def drift_alert(ref, cur, psi_watch=0.1, psi_alert=0.25, ks_alpha=1e-3, ks_min_effect=0.1):
    """
    Alert rule. At ad-platform volumes the KS p-value is tiny for trivial shifts, so
    require an effect size (D >= ks_min_effect) as well as significance.
    Level is 'alert' if PSI >= psi_alert or (p < alpha and D >= min_effect),
    'watch' if PSI >= psi_watch, and 'none' otherwise.
    """
    v = psi(ref, cur)
    D, p = ks_2samp(ref, cur)
    if v >= psi_alert or (p < ks_alpha and D >= ks_min_effect):
        level = "alert"
    elif v >= psi_watch:
        level = "watch"
    else:
        level = "none"
    return {"psi": v, "ks_D": D, "ks_p": p, "level": level}


# ---------------------------------------------------------------------------
# 6. CUSUM change detection on a daily approval-rate stream
# ---------------------------------------------------------------------------
def cusum_rate(successes, trials, p0, k=0.5, h=5.0):
    """
    Prompt: each day we see n_t generated creatives and x_t of them are human-approved.
    The in-control rate is p0, taken from a reference period. Detect a sustained shift
    (for example after a new image model ships) quickly, with few false alarms.

    Standardize z_t = (x_t/n_t - p0) / sqrt(p0 (1 - p0) / n_t), then run two one-sided
    tabular CUSUMs:
        S+_t = max(0, S+_{t-1} + z_t - k),   S-_t = max(0, S-_{t-1} - z_t - k)
    k is the allowance (about half the shift to detect, in sd units) and h is the
    decision interval. Alarm at the first t with S > h. The change point estimate is
    the day after the last day that side's statistic was 0. O(T).
    """
    x = np.asarray(successes, float)
    n = np.asarray(trials, float)
    z = (x / n - p0) / np.sqrt(p0 * (1 - p0) / n)
    T = len(z)
    s_hi, s_lo = np.zeros(T), np.zeros(T)
    hi = lo = 0.0
    alarm, direction, change = None, None, None
    for t in range(T):
        hi = max(0.0, hi + z[t] - k)
        lo = max(0.0, lo - z[t] - k)
        s_hi[t], s_lo[t] = hi, lo
        if alarm is None and (hi > h or lo > h):
            alarm = t
            direction = "up" if hi > h else "down"
            s = s_hi if direction == "up" else s_lo
            zeros = np.nonzero(s[: t + 1] == 0)[0]
            change = int(zeros[-1] + 1) if len(zeros) else 0
    return {"alarm_at": alarm, "direction": direction, "change_point": change, "s_hi": s_hi, "s_lo": s_lo}
    # k=0.5, h=5 gives in-control ARL ~465 days per side and catches a 1-sd shift in
    # ~10 days. If the daily rates are overdispersed (day-of-week, category mix), use
    # a beta-binomial variance or CUSUM the residuals of a seasonal baseline instead.


# ---------------------------------------------------------------------------
# 7. WCAG 2.2 contrast: luminance, ratio, AA checks, text-color pick, scrim alpha
# ---------------------------------------------------------------------------
def srgb_to_linear(c8):
    c = np.asarray(c8, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def relative_luminance(rgb):
    """rgb: (..., 3) in 0-255. L = 0.2126 R + 0.7152 G + 0.0722 B on linearized channels."""
    lin = srgb_to_linear(rgb)
    return lin[..., 0] * 0.2126 + lin[..., 1] * 0.7152 + lin[..., 2] * 0.0722


def contrast_ratio(rgb1, rgb2):
    """(L_lighter + 0.05) / (L_darker + 0.05), in [1, 21]. Broadcasts over pixels."""
    l1, l2 = relative_luminance(rgb1), relative_luminance(rgb2)
    return (np.maximum(l1, l2) + 0.05) / (np.minimum(l1, l2) + 0.05)


def wcag_aa_pass(ratio, large_text=False):
    """
    SC 1.4.3 (AA): 4.5:1 for normal text, 3:1 for large text. Large text means at
    least 18pt (24 CSS px) regular, or at least 14pt (~18.67 CSS px) bold.
    SC 1.4.11 sets 3:1 for non-text UI parts and meaningful graphics. AAA is 7:1 / 4.5:1.
    """
    return bool(np.all(np.asarray(ratio) >= (3.0 if large_text else 4.5)))


def pick_text_color(bg_pixels, brand_colors=(), large_text=False, percentile=1.0):
    """
    Prompt: a headline goes over a region of a generated image. Given that region's
    pixels (N x 3, RGB 0-255), choose the text color: the first brand color that
    passes AA, falling back to white or black. If nothing passes, return None and the
    caller adds a scrim or moves the text.

    A busy background has no single contrast value. Score each candidate by a low
    percentile of its per-pixel contrast, which is robust to a few stray pixels;
    percentile=0 means the strict worst case. O(N * C) for C candidates.
    """
    px = np.asarray(bg_pixels, float).reshape(-1, 3)
    need = 3.0 if large_text else 4.5
    candidates = [tuple(c) for c in brand_colors] + [(255, 255, 255), (0, 0, 0)]
    scored = []
    for c in candidates:
        worst = float(np.percentile(contrast_ratio(px, np.array(c, float)), percentile))
        scored.append((c, worst))
        if worst >= need:
            return {"color": c, "contrast": worst, "scored": scored}
    return {"color": None, "contrast": max(s for _, s in scored), "scored": scored}


def min_scrim_alpha(bg_pixels, text_rgb, overlay_rgb=(0, 0, 0), large_text=False, percentile=1.0, iters=30):
    """
    Follow-up: if no text color passes, find the smallest scrim opacity alpha such that
    text passes over composite = (1 - alpha) * bg + alpha * overlay, composited in
    sRGB space as browsers do. Contrast moves monotonically with alpha when the
    overlay is on the far side of the bg from the text color (dark scrim under white
    text), so binary search works. Returns None if even alpha = 1 fails. O(N * iters).
    """
    px = np.asarray(bg_pixels, float).reshape(-1, 3)
    t, o = np.array(text_rgb, float), np.array(overlay_rgb, float)
    need = 3.0 if large_text else 4.5

    def ok(a):
        comp = (1 - a) * px + a * o
        return np.percentile(contrast_ratio(comp, t), percentile) >= need

    if not ok(1.0):
        return None
    lo, hi = 0.0, 1.0
    if ok(0.0):
        return 0.0
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


# ---------------------------------------------------------------------------
# 8. Saliency-aware smart crop via summed-area table
# ---------------------------------------------------------------------------
def integral_image(a):
    """ii[i, j] = sum of a[:i, :j]; padded with a zero row and column. O(HW)."""
    a = np.asarray(a, float)
    ii = np.zeros((a.shape[0] + 1, a.shape[1] + 1))
    ii[1:, 1:] = a.cumsum(0).cumsum(1)
    return ii


def box_sums(ii, h, w):
    """Sum of every h x w window; out[r, c] = window with top-left (r, c). O(HW) total."""
    return ii[h:, w:] - ii[:-h, w:] - ii[h:, :-w] + ii[:-h, :-w]


def crop_dims(H, W, aspect, scale=1.0):
    """Largest (h, w) with w / h ~= aspect that fits in H x W, times `scale`."""
    if W / H >= aspect:
        h = H
        w = int(round(H * aspect))
    else:
        w = W
        h = int(round(W / aspect))
    return max(1, int(round(h * scale))), max(1, min(W, int(round(w * scale))))


def smart_crop(saliency, aspect, scales=(1.0,), min_retained=0.9):
    """
    Prompt: adapt a 1200x628 hero image to a 1:1 tile or a 9:16 story placement.
    Given a saliency map (product and face likelihood, H x W, non-negative) and a
    target aspect ratio w/h, return the crop window that keeps the most salient mass.

    Brute force re-sums every window: O(HW * hw). With a summed-area table every
    window sum costs O(1), so one crop size costs O(HW) in total.
    Multiple scales: return the tightest crop (smallest scale, so the product is
    largest in a small placement) that still keeps >= min_retained of the total
    saliency; if none does, return the scale-1 crop.
    Returns dict(top, left, h, w, retained).
    """
    S = np.asarray(saliency, float)
    H, W = S.shape
    ii = integral_image(S)
    total = ii[-1, -1] if ii[-1, -1] > 0 else 1.0
    results = []
    for sc in sorted(scales):
        h, w = crop_dims(H, W, aspect, sc)
        sums = box_sums(ii, h, w)
        r, c = np.unravel_index(int(np.argmax(sums)), sums.shape)
        results.append({"top": int(r), "left": int(c), "h": h, "w": w, "scale": sc, "retained": float(sums[r, c] / total)})
    for res in results:  # ascending scale -> tightest first
        if res["retained"] >= min_retained:
            return res
    return results[-1]
    # Extensions to mention: penalize crops that cut through a product bounding box,
    # add a rule-of-thirds prior, and use a per-placement safe zone.


# ---------------------------------------------------------------------------
# 9. Headline placement: largest low-clutter rectangle (maximal rectangle in 0/1 grid)
# ---------------------------------------------------------------------------
def largest_rectangle_histogram(heights):
    """Largest rectangle under a histogram (monotonic stack). Returns (area, left, width, height). O(n)."""
    best = (0, 0, 0, 0)
    stack = []  # indices with increasing heights
    hs = list(heights) + [0]
    for i, hgt in enumerate(hs):
        start = i
        while stack and hs[stack[-1]] >= hgt:
            j = stack.pop()
            left = stack[-1] + 1 if stack else 0
            area = hs[j] * (i - left)
            if area > best[0]:
                best = (area, left, i - left, hs[j])
            start = left
        stack.append(i)
    return best


def maximal_rectangle(free):
    """Largest all-True axis-aligned rectangle. Returns (area, top, left, h, w). O(HW)."""
    F = np.asarray(free, bool)
    H, W = F.shape
    heights = np.zeros(W, dtype=int)
    best = (0, 0, 0, 0, 0)
    for r in range(H):
        heights = np.where(F[r], heights + 1, 0)
        area, left, width, hgt = largest_rectangle_histogram(heights.tolist())
        if area > best[0]:
            best = (area, r - hgt + 1, left, hgt, width)
    return best


def headline_slot(clutter, threshold, blocked_boxes=()):
    """
    Prompt: given a clutter map (edge density or local variance, H x W) for a
    generated background, find the largest-area calm rectangle for the headline. A
    cell is free if clutter < threshold and it is outside every blocked box (product,
    logo, platform UI overlay), with boxes given as (x0, y0, x1, y1), exclusive.
    Reduces to "maximal rectangle in a binary matrix": treat each row as the base of
    a histogram of consecutive free cells above it, and solve each row with a stack.
    O(HW). Brute force is O(H^2 W^2) using prefix sums.
    """
    free = np.asarray(clutter) < threshold
    for x0, y0, x1, y1 in blocked_boxes:
        free[y0:y1, x0:x1] = False
    area, top, left, h, w = maximal_rectangle(free)
    return {"area": area, "top": top, "left": left, "h": h, "w": w}
    # Real version: maximize area subject to aspect bounds and a minimum height for
    # the font size, then run drill 7 on the chosen region's pixels.


# ---------------------------------------------------------------------------
# 10. Product fidelity: SSIM from scratch + perceptual hashes (aHash / dHash)
# ---------------------------------------------------------------------------
def rgb_to_gray(img):
    img = np.asarray(img, float)
    return img[..., 0] * 0.299 + img[..., 1] * 0.587 + img[..., 2] * 0.114


def _gauss_kernel(size=11, sigma=1.5):
    x = np.arange(size) - (size - 1) / 2
    g = np.exp(-(x**2) / (2 * sigma**2))
    return g / g.sum()


def _filter_valid(x, k):
    """Separable 'valid' filter: one K-tap 1-D pass per axis. O(HW * K)."""
    K = len(k)
    H, W = x.shape
    rows = sum(k[t] * x[:, t : W - K + 1 + t] for t in range(K))
    return sum(k[t] * rows[t : H - K + 1 + t, :] for t in range(K))


def ssim(x, y, data_range=255.0, win=11, sigma=1.5):
    """
    Prompt: the generator re-renders the advertiser's product into a new scene. Check
    that the product crop still matches the source packshot. Implement SSIM on
    grayscale with an 11x11 Gaussian window (sigma 1.5):
        SSIM = ((2 mu_x mu_y + C1)(2 s_xy + C2)) / ((mu_x^2 + mu_y^2 + C1)(s_x^2 + s_y^2 + C2))
        C1 = (0.01 L)^2, C2 = (0.03 L)^2, where L is the data range.
    Returns the mean of the SSIM map. O(HW * win) with separable filtering.
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    k = _gauss_kernel(win, sigma)
    C1, C2 = (0.01 * data_range) ** 2, (0.03 * data_range) ** 2
    mx, my = _filter_valid(x, k), _filter_valid(y, k)
    sxx = _filter_valid(x * x, k) - mx * mx
    syy = _filter_valid(y * y, k) - my * my
    sxy = _filter_valid(x * y, k) - mx * my
    num = (2 * mx * my + C1) * (2 * sxy + C2)
    den = (mx * mx + my * my + C1) * (sxx + syy + C2)
    return float(np.mean(num / den))


def _area_resize(img, out_h, out_w):
    """Downsample by averaging over (possibly uneven) blocks using an integral image."""
    ii = integral_image(img)
    H, W = np.asarray(img).shape
    rs = np.linspace(0, H, out_h + 1).round().astype(int)
    cs = np.linspace(0, W, out_w + 1).round().astype(int)
    out = np.empty((out_h, out_w))
    for i in range(out_h):
        for j in range(out_w):
            r0, r1, c0, c1 = rs[i], rs[i + 1], cs[j], cs[j + 1]
            s = ii[r1, c1] - ii[r0, c1] - ii[r1, c0] + ii[r0, c0]
            out[i, j] = s / max(1, (r1 - r0) * (c1 - c0))
    return out


def ahash(gray, n=8):
    """Average hash: resize to n x n, bit = pixel > mean. 64 bits for n=8."""
    small = _area_resize(gray, n, n)
    return (small > small.mean()).ravel()


def dhash(gray, n=8, min_diff=1.0):
    """
    Difference hash: resize to n x (n+1), bit = (right - left) > min_diff. Encodes
    gradients. The textbook version uses min_diff=0, but then flat regions (packshot
    backgrounds) produce bits that are coin flips under noise or compression; a small
    dead-band makes those bits a stable 0.
    """
    small = _area_resize(gray, n, n + 1)
    return ((small[:, 1:] - small[:, :-1]) > min_diff).ravel()


def hamming(a, b):
    return int(np.count_nonzero(np.asarray(a) != np.asarray(b)))
    # Hashes are cheap first-pass filters (and give near-dupe keys, see drill 14):
    # robust to blur and rescaling, weak on fine detail. SSIM catches structural
    # change. At Walmart scale: hash or embed everything, run SSIM / OCR / logo
    # checks only on candidates, and calibrate the thresholds against human labels
    # of "product misrepresented".


# ---------------------------------------------------------------------------
# 11. Brand palette adherence: sRGB -> CIELAB (D65), Delta E 76/94, seeded k-means
# ---------------------------------------------------------------------------
_M_RGB2XYZ = np.array(
    [[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]]
)
_WHITE_D65 = np.array([0.95047, 1.0, 1.08883])


def srgb_to_lab(rgb):
    """(..., 3) sRGB 0-255 -> CIELAB (L*, a*, b*) under D65 / 2 degree observer."""
    xyz = srgb_to_linear(rgb) @ _M_RGB2XYZ.T
    t = xyz / _WHITE_D65
    d = 6.0 / 29.0
    f = np.where(t > d**3, np.cbrt(t), t / (3 * d * d) + 4.0 / 29.0)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def delta_e76(lab1, lab2):
    """Euclidean distance in Lab. ~2.3 is a just-noticeable difference."""
    return np.linalg.norm(np.asarray(lab1, float) - np.asarray(lab2, float), axis=-1)


def delta_e94(lab_ref, lab):
    """CIE94 (graphic arts: kL=1, K1=0.045, K2=0.015). Not symmetric: lab_ref is the reference."""
    lab_ref, lab = np.asarray(lab_ref, float), np.asarray(lab, float)
    dL = lab_ref[..., 0] - lab[..., 0]
    C1 = np.hypot(lab_ref[..., 1], lab_ref[..., 2])
    C2 = np.hypot(lab[..., 1], lab[..., 2])
    dC = C1 - C2
    da = lab_ref[..., 1] - lab[..., 1]
    db = lab_ref[..., 2] - lab[..., 2]
    dH2 = np.maximum(da**2 + db**2 - dC**2, 0.0)
    SC = 1 + 0.045 * C1
    SH = 1 + 0.015 * C1
    return np.sqrt(dL**2 + (dC / SC) ** 2 + dH2 / SH**2)


def kmeans(X, k, rng, n_iter=50):
    """
    Lloyd's algorithm with k-means++ seeding. An empty cluster is re-seeded at the
    point farthest from its assigned center. O(n k d) per iteration.
    Returns (centers, labels).
    """
    X = np.asarray(X, float)
    n = len(X)
    centers = [X[rng.integers(n)]]
    d2 = np.sum((X - centers[0]) ** 2, axis=1)
    for _ in range(1, k):
        probs = d2 / d2.sum() if d2.sum() > 0 else np.full(n, 1.0 / n)
        centers.append(X[rng.choice(n, p=probs)])
        d2 = np.minimum(d2, np.sum((X - centers[-1]) ** 2, axis=1))
    C = np.array(centers)
    labels = np.zeros(n, dtype=int)
    for it in range(n_iter):
        D = ((X[:, None, :] - C[None, :, :]) ** 2).sum(-1)
        new = D.argmin(1)
        if it > 0 and np.array_equal(new, labels):
            break
        labels = new
        for j in range(k):
            m = labels == j
            if m.any():
                C[j] = X[m].mean(0)
            else:
                C[j] = X[D.min(1).argmax()]
    return C, labels


def palette_adherence(img_rgb, brand_rgb, k=5, tol=10.0, min_weight=0.05, seed=0, metric="de76"):
    """
    Prompt: an advertiser gives a brand palette. Does a generated creative stay on
    brand? Extract the dominant colors with k-means in CIELAB (a roughly perceptually
    uniform space, unlike RGB). Match each dominant color to its nearest brand color
    by Delta E. Report the on-brand pixel share and flag any off-brand dominant color
    that covers >= min_weight of the image.
    """
    lab = srgb_to_lab(np.asarray(img_rgb, float).reshape(-1, 3))
    brand_lab = srgb_to_lab(np.asarray(brand_rgb, float))
    C, labels = kmeans(lab, k, np.random.default_rng(seed))
    weights = np.bincount(labels, minlength=k) / len(labels)
    clusters, on_brand, violations = [], 0.0, []
    for j in range(k):
        if weights[j] == 0:
            continue
        if metric == "de94":
            de = delta_e94(brand_lab, C[j][None, :])
        else:
            de = delta_e76(brand_lab, C[j][None, :])
        nearest = int(np.argmin(de))
        info = {"lab": C[j], "weight": float(weights[j]), "nearest_brand": nearest, "delta_e": float(de[nearest])}
        clusters.append(info)
        if de[nearest] <= tol:
            on_brand += weights[j]
        elif weights[j] >= min_weight:
            violations.append(info)
    return {"on_brand_share": float(on_brand), "clusters": clusters, "violations": violations}
    # Use CIEDE2000 in production for its better hue handling around blue. Downsample
    # pixels before k-means (or use mini-batch k-means), and mask out the product
    # region, whose colors belong to the product and not to the brand.


# ---------------------------------------------------------------------------
# 12. Bounding-box layout validator
# ---------------------------------------------------------------------------
def box_area(b):
    x0, y0, x1, y1 = b
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def intersection(a, b):
    return box_area((max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])))


def iou(a, b):
    inter = intersection(a, b)
    union = box_area(a) + box_area(b) - inter
    return inter / union if union > 0 else 0.0


def contains(outer, inner):
    return outer[0] <= inner[0] and outer[1] <= inner[1] and inner[2] <= outer[2] and inner[3] <= outer[3]


def validate_layout(
    canvas_wh,
    elements,
    safe_margin=0.05,
    min_logo_frac=0.01,
    min_logo_px=32,
    max_text_product_overlap=0.0,
    min_target_px=24,
    min_product_frac=0.10,
):
    """
    Prompt: a layout model places elements on a canvas. Each element is a dict
    {"id", "kind" in {product, logo, text, cta}, "box": (x0, y0, x1, y1)} in pixels.
    Write a validator that returns every rule violation as (rule, id, detail):
      - safe_zone:        every element lies inside the canvas inset by safe_margin
      - logo_too_small:   logo area >= min_logo_frac of the canvas and both sides >= min_logo_px
      - text_over_product: intersection(text, product) / area(text) <= max_text_product_overlap
      - text_over_logo:   no text intersects a logo
      - cta_target_size:  CTA >= 24 x 24 CSS px (WCAG 2.2 SC 2.5.8 Target Size, Minimum)
      - product_missing / product_too_small: a product exists and covers >= min_product_frac
    O(E^2) pairwise checks; E is small. For many elements, use a sweep line or R-tree.
    """
    W, H = canvas_wh
    mx, my = safe_margin * W, safe_margin * H
    safe = (mx, my, W - mx, H - my)
    canvas_area = W * H
    v = []
    by_kind = defaultdict(list)
    for e in elements:
        by_kind[e["kind"]].append(e)
        if not contains(safe, e["box"]):
            v.append(("safe_zone", e["id"], "outside safe zone"))
    for lg in by_kind["logo"]:
        x0, y0, x1, y1 = lg["box"]
        if box_area(lg["box"]) < min_logo_frac * canvas_area or min(x1 - x0, y1 - y0) < min_logo_px:
            v.append(("logo_too_small", lg["id"], f"{x1 - x0}x{y1 - y0}"))
    for t in by_kind["text"]:
        ta = box_area(t["box"])
        for p in by_kind["product"]:
            frac = intersection(t["box"], p["box"]) / ta if ta > 0 else 0.0
            if frac > max_text_product_overlap:
                v.append(("text_over_product", t["id"], f"{frac:.0%} of text covers {p['id']}"))
        for lg in by_kind["logo"]:
            if intersection(t["box"], lg["box"]) > 0:
                v.append(("text_over_logo", t["id"], lg["id"]))
    for c in by_kind["cta"]:
        x0, y0, x1, y1 = c["box"]
        if (x1 - x0) < min_target_px or (y1 - y0) < min_target_px:
            v.append(("cta_target_size", c["id"], f"{x1 - x0}x{y1 - y0}"))
    if not by_kind["product"]:
        v.append(("product_missing", None, ""))
    for p in by_kind["product"]:
        if box_area(p["box"]) < min_product_frac * canvas_area:
            v.append(("product_too_small", p["id"], f"{box_area(p['box']) / canvas_area:.1%}"))
    return v


# ---------------------------------------------------------------------------
# 13. Thompson sampling (Beta-Bernoulli) + top-two Thompson sampling
# ---------------------------------------------------------------------------
def thompson_choose(alpha, beta, rng):
    """Sample theta_k ~ Beta(alpha_k, beta_k) and play the argmax. O(K) per round."""
    return int(np.argmax(rng.beta(alpha, beta)))


def top_two_thompson_choose(alpha, beta, rng, leader_prob=0.5, max_tries=100):
    """
    Top-two Thompson sampling (Russo 2016), for best-arm identification rather than
    regret. With probability leader_prob play the TS leader; otherwise resample until
    a different arm wins and play that challenger. This keeps measuring the runner-up,
    so P(best) concentrates faster for a fixed budget. That fits a creative test whose
    goal is to pick a winner and ship it.
    """
    leader = thompson_choose(alpha, beta, rng)
    if rng.random() < leader_prob:
        return leader
    for _ in range(max_tries):
        c = thompson_choose(alpha, beta, rng)
        if c != leader:
            return c
    th = rng.beta(alpha, beta)  # fallback: runner-up in one draw
    th[leader] = -np.inf
    return int(np.argmax(th))


def prob_best(alpha, beta, rng, n_draws=20000):
    """Monte Carlo P(arm k has the highest rate | data). O(n_draws * K)."""
    draws = rng.beta(np.asarray(alpha)[None, :], np.asarray(beta)[None, :], size=(n_draws, len(alpha)))
    return np.bincount(draws.argmax(1), minlength=len(alpha)) / n_draws


def run_bandit(true_rates, chooser, n_rounds, rng, prior=(1.0, 1.0)):
    """
    Prompt: K generated creative variants with unknown CTR. Allocate impressions
    adaptively. Returns (alpha, beta, pulls).
    """
    K = len(true_rates)
    a = np.full(K, prior[0])
    b = np.full(K, prior[1])
    pulls = np.zeros(K, dtype=int)
    for _ in range(n_rounds):
        k = chooser(a, b, rng)
        r = rng.random() < true_rates[k]
        a[k] += r
        b[k] += 1 - r
        pulls[k] += 1
    return a, b, pulls
    # Production: batched / delayed updates (posterior refresh every N minutes), a
    # floor allocation per variant for guardrail metrics, and a stopping rule such as
    # P(best) > 0.95 or expected loss < epsilon. Also watch for novelty effects.


# ---------------------------------------------------------------------------
# 14. Near-duplicate creative dedupe: cosine similarity + union-find
# ---------------------------------------------------------------------------
class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path halving
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return True


def dedupe_creatives(emb, threshold=0.9, quality=None, block=1024):
    """
    Prompt: the generator produced thousands of variants and many are near-identical.
    Given L2-normalizable embeddings (n x d), cluster the pairs with cosine >= threshold
    (taking the transitive closure via union-find) and keep one representative per
    cluster: the one with the highest quality score, or the lowest index if no scores.
    Returns (clusters as sorted index lists, keep indices).

    Exact: O(n^2 d) similarity in row blocks (memory O(block * n)), plus near-O(1)
    amortized union-find operations. At scale: ANN (HNSW / IVF) or SimHash LSH to
    generate candidate pairs, then verify. Caveat: the transitive closure can chain
    A~B~C even when A and C differ; if that matters, use complete-linkage or
    re-verify each cluster against its representative.
    """
    E = np.asarray(emb, float)
    E = E / np.linalg.norm(E, axis=1, keepdims=True)
    n = len(E)
    uf = UnionFind(n)
    for s in range(0, n, block):
        S = E[s : s + block] @ E.T
        ii, jj = np.nonzero(S >= threshold)
        for i, j in zip(ii + s, jj):
            if i < j:
                uf.union(int(i), int(j))
    groups = defaultdict(list)
    for i in range(n):
        groups[uf.find(i)].append(i)
    clusters = sorted(sorted(g) for g in groups.values())
    q = np.zeros(n) if quality is None else np.asarray(quality, float)
    keep = sorted(max(g, key=lambda i: (q[i], -i)) for g in clusters)
    return clusters, keep


# ===========================================================================
# Self-tests (simulated data with known ground truth; seeded -> deterministic)
# ===========================================================================
def _tests():
    passed = 0

    # ---- 1. Bradley-Terry + Elo -------------------------------------------
    rng = np.random.default_rng(1)
    n_items = 10
    theta_true = rng.permutation(np.linspace(-1.5, 1.5, n_items))
    wins = np.zeros((n_items, n_items))
    matches = []
    for _ in range(6000):
        i, j = rng.choice(n_items, 2, replace=False)
        i_wins = rng.random() < _sigmoid(theta_true[i] - theta_true[j])
        w, l = (i, j) if i_wins else (j, i)
        wins[w, l] += 1
        matches.append((int(i), int(j), 1.0 if i_wins else 0.0))
    th = bradley_terry_mm(wins)
    assert np.argmax(th) == np.argmax(theta_true)
    assert spearman(th, theta_true) > 0.95
    assert np.max(np.abs(th - (theta_true - theta_true.mean()))) < 0.25
    elo = elo_stream(n_items, matches, k=16)
    assert spearman(elo, theta_true) > 0.85
    a2, b2 = elo_update(1500, 1500, 1.0, k=32)
    assert abs(a2 - 1516) < 1e-9 and abs(b2 - 1484) < 1e-9
    passed += 1

    # ---- 2. Agreement metrics ---------------------------------------------
    # Hand example: confusion [[20, 5], [10, 15]] -> p_o = 0.7, p_e = 0.5, kappa = 0.4
    a = [1] * 20 + [1] * 5 + [0] * 10 + [0] * 15
    b = [1] * 20 + [0] * 5 + [1] * 10 + [0] * 15
    assert abs(percent_agreement(a, b) - 0.7) < 1e-12
    assert abs(cohen_kappa(a, b) - 0.4) < 1e-12
    # Simulated judge: balanced human labels, judge flips 20% -> kappa ~ 0.6
    rng = np.random.default_rng(2)
    human = rng.integers(0, 2, 8000)
    judge = np.where(rng.random(8000) < 0.2, 1 - human, human)
    assert abs(cohen_kappa(human, judge) - 0.6) < 0.04
    # Imbalance: 95% approve, judge always says approve -> 95% agreement, kappa 0
    hum = (rng.random(4000) < 0.95).astype(int)
    assert percent_agreement(hum, np.ones(4000, int)) > 0.93 and abs(cohen_kappa(hum, np.ones(4000, int))) < 1e-12
    # QWK: perfect = 1; off-by-one beats off-by-four
    r = rng.integers(0, 5, 2000)
    assert abs(quadratic_weighted_kappa(r, r, 5) - 1) < 1e-12
    near = np.clip(r + rng.choice([-1, 0, 1], 2000), 0, 4)
    far = rng.integers(0, 5, 2000)
    assert quadratic_weighted_kappa(r, near, 5) > 0.8 > 0.1 > quadratic_weighted_kappa(r, far, 5)
    # Spearman with ties: hand-computed 4.5 / sqrt(4.5 * 5)
    assert np.allclose(rankdata_avg([1, 2, 2, 3]), [1, 2.5, 2.5, 4])
    assert abs(spearman([1, 2, 2, 3], [1, 3, 2, 4]) - 4.5 / math.sqrt(22.5)) < 1e-12
    xs = rng.normal(size=300)
    assert abs(spearman(xs, np.exp(xs)) - 1) < 1e-12 and abs(spearman(xs, -(xs**3)) + 1) < 1e-12
    passed += 1

    # ---- 3. Calibration + routing -----------------------------------------
    rng = np.random.default_rng(3)

    def sim(n):
        s = rng.random(n)
        p_true = _sigmoid(10 * (s - 0.6))  # raw score is NOT a probability
        return s, (rng.random(n) < p_true).astype(float), p_true

    s_tr, y_tr, _ = sim(20000)
    s_te, y_te, p_te = sim(20000)
    bx, bv = pav_fit(s_tr, y_tr)
    assert np.all(np.diff(bv) >= -1e-12)  # monotone
    cal_te = pav_predict(bx, bv, s_te)
    assert ece(y_te, s_te) > 0.08 and ece(y_te, cal_te) < 0.02
    assert np.mean(np.abs(cal_te - p_te)) < 0.03
    route = auto_approve_threshold(s_tr, y_tr, target_precision=0.95)
    auto = s_te >= route["threshold"]
    held_prec = y_te[auto].mean()
    held_rec = y_te[auto].sum() / y_te.sum()
    assert held_prec >= 0.94, held_prec  # holds out of sample
    assert 0.15 < held_rec < 0.6 and abs(held_rec - route["recall"]) < 0.05
    # Threshold lands where the true P(approve) is still high (sigmoid(10*(t-0.6)))
    assert 0.8 < route["threshold"] < 0.95
    loose = auto_approve_threshold(s_tr, y_tr, target_precision=0.80)
    assert loose["recall"] > route["recall"]  # precision/recall tradeoff
    passed += 1

    # ---- 4. Position bias -------------------------------------------------
    rng = np.random.default_rng(4)
    n = 4000
    d = rng.normal(0, 1.0, n)  # true logit gap a - b
    beta = 0.7
    p_ab = _sigmoid(d + beta + rng.normal(0, 0.3, n))
    p_ba = _sigmoid(-d + beta + rng.normal(0, 0.3, n))
    rep = position_bias_report(p_ab, p_ba)
    assert abs(rep["beta_logit"] - beta) < 0.05
    assert rep["bias"] > 0.08
    truth = d > 0
    acc_single = np.mean((p_ab > 0.5) == truth)
    acc_debiased = np.mean((rep["debiased_pref"] > 0.5) == truth)
    assert acc_debiased > acc_single + 0.05
    inc = rep["inconsistent"]
    assert 0.3 < inc.mean() < 0.7  # ~P(|d| < beta): a strong bias flips half the calls
    assert np.abs(d[inc]).mean() < 0.5 * np.abs(d[~inc]).mean()  # flips occur on close calls
    # Binary verdicts: an unbiased judge -> first-slot rate ~ 0.5
    v_ab = (rng.random(n) < _sigmoid(d)).astype(float)
    v_ba = (rng.random(n) < _sigmoid(-d)).astype(float)
    assert abs(position_bias_report(v_ab, v_ba)["bias"]) < 0.02
    passed += 1

    # ---- 5. Drift: PSI + KS -----------------------------------------------
    rng = np.random.default_rng(5)
    small_a, small_b = rng.normal(size=37), rng.normal(0.3, 1, size=53)
    grid = np.concatenate([small_a, small_b])
    brute = max(abs(np.mean(small_a <= g) - np.mean(small_b <= g)) for g in grid)
    assert abs(ks_2samp(small_a, small_b)[0] - brute) < 1e-12
    ref = rng.beta(5, 2, 20000)
    same = rng.beta(5, 2, 20000)
    shifted = np.clip(rng.beta(5, 2, 20000) - 0.08, 0, 1)
    assert psi(ref, ref) < 1e-9
    r0 = drift_alert(ref, same)
    assert r0["level"] == "none" and r0["psi"] < 0.01 and r0["ks_p"] > 0.01
    r1 = drift_alert(ref, shifted)
    assert r1["level"] == "alert" and r1["psi"] > 0.25 and r1["ks_D"] > 0.1
    # Tiny shift at huge n: KS significant but below effect floor -> not an alert
    tiny = rng.beta(5, 2, 20000) - 0.01
    r2 = drift_alert(ref, tiny)
    assert r2["ks_p"] < 1e-3 and r2["level"] != "alert"
    passed += 1

    # ---- 6. CUSUM ---------------------------------------------------------
    rng = np.random.default_rng(6)
    T, n_day, p0 = 60, 500, 0.80
    trials = np.full(T, n_day)
    stable = rng.binomial(n_day, p0, T)
    assert cusum_rate(stable, trials, p0)["alarm_at"] is None
    rates = np.where(np.arange(T) < 40, p0, 0.76)  # ~2.2 sd drop per day from day 40
    drop = rng.binomial(n_day, rates)
    res = cusum_rate(drop, trials, p0)
    assert res["direction"] == "down" and 40 <= res["alarm_at"] <= 46
    assert abs(res["change_point"] - 40) <= 3
    up = rng.binomial(n_day, np.where(np.arange(T) < 30, p0, 0.84))
    assert cusum_rate(up, trials, p0)["direction"] == "up"
    passed += 1

    # ---- 7. WCAG contrast -------------------------------------------------
    white, black = np.array([255, 255, 255]), np.array([0, 0, 0])
    assert abs(contrast_ratio(white, black) - 21.0) < 1e-9
    assert abs(contrast_ratio(white, white) - 1.0) < 1e-12
    assert abs(relative_luminance(white) - 1.0) < 1e-12
    c767 = float(contrast_ratio([0x76] * 3, white))
    c777 = float(contrast_ratio([0x77] * 3, white))
    assert abs(c767 - 4.54) < 0.01 and wcag_aa_pass(c767)  # the classic boundary gray
    assert abs(c777 - 4.48) < 0.01 and not wcag_aa_pass(c777) and wcag_aa_pass(c777, large_text=True)
    rng = np.random.default_rng(7)
    yellow, blue = (255, 194, 32), (0, 83, 226)
    navy_bg = np.clip(np.array([20, 30, 60]) + rng.normal(0, 8, (500, 3)), 0, 255)
    light_bg = np.clip(np.array([240, 240, 235]) + rng.normal(0, 6, (500, 3)), 0, 255)
    assert pick_text_color(navy_bg, [yellow, blue])["color"] == yellow  # brand color first
    assert pick_text_color(light_bg, [yellow, blue])["color"] == blue
    assert pick_text_color(light_bg)["color"] == (0, 0, 0)
    busy = np.vstack([np.tile(white, (250, 1)), np.tile(black, (250, 1))])  # half and half
    assert pick_text_color(busy, [yellow, blue])["color"] is None
    alpha = min_scrim_alpha(busy, (255, 255, 255))
    assert 0.4 < alpha < 0.7  # analytic: white text needs bg L <= 0.183 -> ~0.535
    comp = (1 - alpha) * busy + alpha * black
    assert wcag_aa_pass(np.percentile(contrast_ratio(comp, white), 1.0))
    passed += 1

    # ---- 8. Smart crop ----------------------------------------------------
    rng = np.random.default_rng(8)
    sm = rng.random((12, 15))
    ii = integral_image(sm)
    bs = box_sums(ii, 4, 6)
    brute = np.array([[sm[r : r + 4, c : c + 6].sum() for c in range(10)] for r in range(9)])
    assert np.allclose(bs, brute)
    H, W = 100, 200
    yy, xx = np.mgrid[:H, :W]
    sal = np.exp(-((yy - 40) ** 2 + (xx - 150) ** 2) / (2 * 8.0**2)) + 0.001 * rng.random((H, W))
    sq = smart_crop(sal, aspect=1.0)
    assert (sq["h"], sq["w"]) == (100, 100) and sq["left"] <= 150 - 20 and sq["left"] + 100 >= 150 + 20
    assert sq["retained"] > 0.95
    story = smart_crop(sal, aspect=9 / 16)
    assert story["h"] == 100 and story["left"] <= 150 <= story["left"] + story["w"]
    tight = smart_crop(sal, aspect=1.0, scales=(0.4, 0.6, 0.8, 1.0), min_retained=0.9)
    assert tight["scale"] < 1.0 and tight["retained"] >= 0.9
    assert tight["top"] <= 40 <= tight["top"] + tight["h"] and tight["left"] <= 150 <= tight["left"] + tight["w"]
    passed += 1

    # ---- 9. Maximal rectangle / headline slot -----------------------------
    rng = np.random.default_rng(9)

    def brute_max_rect(F):
        P = integral_image(F.astype(float))
        best = 0
        Hh, Ww = F.shape
        for r0 in range(Hh):
            for r1 in range(r0 + 1, Hh + 1):
                for c0 in range(Ww):
                    for c1 in range(c0 + 1, Ww + 1):
                        area = (r1 - r0) * (c1 - c0)
                        if area > best and P[r1, c1] - P[r0, c1] - P[r1, c0] + P[r0, c0] == area:
                            best = area
        return best

    for _ in range(40):
        F = rng.random((6, 7)) < rng.uniform(0.4, 0.9)
        area, top, left, h, w = maximal_rectangle(F)
        assert area == brute_max_rect(F)
        if area:
            assert F[top : top + h, left : left + w].all() and h * w == area
    assert largest_rectangle_histogram([2, 1, 5, 6, 2, 3])[0] == 10
    clutter = 0.5 + 0.5 * rng.random((60, 160))
    clutter[10:30, 50:120] = 0.1 * rng.random((20, 70))  # the calm region
    slot = headline_slot(clutter, threshold=0.3)
    assert (slot["top"], slot["left"], slot["h"], slot["w"]) == (10, 50, 20, 70)
    slot2 = headline_slot(clutter, 0.3, blocked_boxes=[(50, 10, 80, 30)])  # product on the left part
    assert (slot2["left"], slot2["w"], slot2["h"]) == (80, 40, 20)
    passed += 1

    # ---- 10. Product fidelity ---------------------------------------------
    rng = np.random.default_rng(10)
    S = 64
    img = np.full((S, S, 3), 245.0)
    img[12:52, 16:48] = [200, 40, 40]  # red box (product)
    img[20:24, 16:48] = [250, 220, 60]  # yellow stripe
    yy, xx = np.mgrid[:S, :S]
    img[(yy - 36) ** 2 + (xx - 32) ** 2 < 49] = [30, 60, 180]  # blue logo disc
    img[42:50, 20:44] += rng.normal(0, 25, (8, 24, 1))  # label "text" texture
    img = np.clip(img, 0, 255)
    g = rgb_to_gray(img)
    blur = np.pad(g, 2, mode="edge")
    blur = sum(blur[i : i + S, j : j + S] for i in range(5) for j in range(5)) / 25.0
    shifted = np.roll(g, (5, 7), axis=(0, 1))
    shifted[:5, :] = 245.0
    shifted[:, :7] = 245.0
    recol = img.copy()
    recol[12:52, 16:48] = recol[12:52, 16:48][..., ::-1]  # swap R and B on the product
    recol_g = rgb_to_gray(recol)
    mild = np.clip(g + rng.normal(0, 2, g.shape), 0, 255)
    assert abs(ssim(g, g) - 1.0) < 1e-12 and hamming(ahash(g), ahash(g)) == 0
    s_mild, s_blur, s_shift, s_rec = ssim(g, mild), ssim(g, blur), ssim(g, shifted), ssim(g, recol_g)
    assert s_mild > 0.9
    assert s_shift < s_blur < s_mild and s_shift < 0.6 and s_rec < 0.9 and s_blur < 0.9
    for hf in (ahash, dhash):
        assert hamming(hf(g), hf(mild)) <= 2
        assert hamming(hf(g), hf(blur)) <= 2  # hashes are blur-robust; SSIM is what catches blur
        assert hamming(hf(g), hf(shifted)) >= 8
    assert hamming(dhash(g), dhash(recol_g)) >= 4  # recolor changes the gradient structure
    assert hamming(ahash(g), ahash(recol_g)) <= 2  # blind spot: aHash on gray misses hue swaps
    passed += 1

    # ---- 11. Palette adherence --------------------------------------------
    assert np.allclose(srgb_to_lab([255, 255, 255]), [100, 0, 0], atol=1e-3)
    assert np.allclose(srgb_to_lab([0, 0, 0]), [0, 0, 0], atol=1e-9)
    assert np.allclose(srgb_to_lab([255, 0, 0]), [53.24, 80.09, 67.20], atol=0.05)
    l1, l2 = srgb_to_lab([200, 40, 40]), srgb_to_lab([190, 60, 50])
    assert abs(delta_e76(l1, l2) - delta_e76(l2, l1)) < 1e-12
    assert delta_e94(l1, l2) < delta_e76(l1, l2)  # chroma/hue weighting shrinks saturated diffs
    rng = np.random.default_rng(11)
    brand = np.array([[0, 83, 226], [255, 194, 32], [255, 255, 255]])
    on = np.zeros((40, 60, 3))
    on[:, :30] = brand[0]
    on[:, 30:45] = brand[1]
    on[:, 45:] = brand[2]
    on = np.clip(on + rng.normal(0, 3, on.shape), 0, 255)
    res_on = palette_adherence(on, brand, k=4)
    assert res_on["on_brand_share"] > 0.98 and not res_on["violations"]
    off = on.copy()
    off[:, 45:] = np.clip(np.array([40, 170, 70]) + rng.normal(0, 3, (40, 15, 3)), 0, 255)  # off-brand green
    res_off = palette_adherence(off, brand, k=4, metric="de94")
    assert len(res_off["violations"]) == 1 and abs(res_off["violations"][0]["weight"] - 0.25) < 0.02
    assert abs(res_off["on_brand_share"] - 0.75) < 0.02
    C, lab_ = kmeans(np.r_[rng.normal(0, 0.1, (100, 2)), rng.normal(5, 0.1, (100, 2))], 2, np.random.default_rng(0))
    assert len(set(lab_[:100])) == 1 and len(set(lab_[100:])) == 1 and lab_[0] != lab_[150]
    passed += 1

    # ---- 12. Layout validator ---------------------------------------------
    assert abs(iou((0, 0, 10, 10), (5, 5, 15, 15)) - 25 / 175) < 1e-12
    assert iou((0, 0, 1, 1), (2, 2, 3, 3)) == 0.0 and iou((0, 0, 4, 4), (0, 0, 4, 4)) == 1.0
    good = [
        {"id": "prod", "kind": "product", "box": (520, 80, 1000, 560)},
        {"id": "logo", "kind": "logo", "box": (80, 60, 240, 140)},
        {"id": "head", "kind": "text", "box": (80, 200, 480, 320)},
        {"id": "cta", "kind": "cta", "box": (80, 420, 280, 480)},
    ]
    assert validate_layout((1200, 628), good) == []
    bad = [
        {"id": "prod", "kind": "product", "box": (520, 80, 1000, 560)},
        {"id": "logo", "kind": "logo", "box": (10, 10, 40, 30)},  # tiny and in the margin
        {"id": "head", "kind": "text", "box": (400, 200, 700, 320)},  # runs over the product
        {"id": "sub", "kind": "text", "box": (30, 20, 200, 60)},  # over logo, outside safe zone
        {"id": "cta", "kind": "cta", "box": (80, 420, 160, 440)},  # 20 px tall < 24
    ]
    got = {(r, i) for r, i, _ in validate_layout((1200, 628), bad)}
    assert got == {
        ("safe_zone", "logo"),
        ("safe_zone", "sub"),
        ("logo_too_small", "logo"),
        ("text_over_product", "head"),
        ("text_over_logo", "sub"),
        ("cta_target_size", "cta"),
    }, got
    assert ("product_missing", None) in {(r, i) for r, i, _ in validate_layout((1200, 628), good[1:])}
    passed += 1

    # ---- 13. Thompson / top-two Thompson ----------------------------------
    true_rates = np.array([0.10, 0.12, 0.15, 0.20, 0.11])
    best = int(np.argmax(true_rates))
    a_ts, b_ts, pulls_ts = run_bandit(true_rates, thompson_choose, 4000, np.random.default_rng(13))
    a_tt, b_tt, pulls_tt = run_bandit(true_rates, top_two_thompson_choose, 4000, np.random.default_rng(13))
    assert np.argmax(pulls_ts) == best and np.argmax(pulls_tt) == best
    assert pulls_ts[best] > 0.6 * 4000  # TS exploits
    assert pulls_tt[best] < pulls_ts[best]  # TTTS keeps measuring challengers
    assert 0.4 < pulls_tt[best] / 4000 < 0.6  # ~leader_prob of traffic on the leader
    pb_ts = prob_best(a_ts, b_ts, np.random.default_rng(0))
    pb_tt = prob_best(a_tt, b_tt, np.random.default_rng(0))
    assert np.argmax(pb_ts) == best and np.argmax(pb_tt) == best and pb_tt[best] > 0.95
    assert abs(prob_best(np.array([5.0, 5.0]), np.array([5.0, 5.0]), np.random.default_rng(1))[0] - 0.5) < 0.02
    passed += 1

    # ---- 14. Near-duplicate dedupe ----------------------------------------
    rng = np.random.default_rng(14)
    n_base, dim = 30, 64
    base = rng.normal(size=(n_base, dim))
    base /= np.linalg.norm(base, axis=1, keepdims=True)
    embs, truth_id = [], []
    for c in range(n_base):
        for _ in range(int(rng.integers(1, 5))):
            embs.append(base[c] + 0.03 * rng.normal(size=dim))
            truth_id.append(c)
    embs, truth_id = np.array(embs), np.array(truth_id)
    perm = rng.permutation(len(embs))
    embs, truth_id = embs[perm], truth_id[perm]
    quality = rng.random(len(embs))
    clusters, keep = dedupe_creatives(embs, threshold=0.9, quality=quality, block=16)
    want = sorted(sorted(np.nonzero(truth_id == c)[0].tolist()) for c in range(n_base))
    assert clusters == want
    assert len(keep) == n_base
    for g_ in clusters:
        assert max(g_, key=lambda i: quality[i]) in keep
    uf = UnionFind(4)
    assert uf.union(0, 1) and uf.union(2, 3) and uf.union(1, 3) and not uf.union(0, 2)
    passed += 1

    print(f"All {passed} creative drills pass.")


if __name__ == "__main__":
    _tests()
