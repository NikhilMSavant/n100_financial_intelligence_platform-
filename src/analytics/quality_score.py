"""
quality_score.py
----------------
Day 12: composite_quality_score - not a formula given explicitly in the
spec, so this is a documented, defensible combination of 4 signals we
already compute elsewhere: ROE, Debt-to-Equity, Interest Coverage, and
single-year CFO/PAT quality. Each is normalized to a 0-100 scale (higher
is always better), then averaged across whichever signals are available
for that row. Returns None only if NONE of the 4 signals are available.
"""


def _scale(value, low, high):
    """Linearly scales value into [0, 100], clamped at the ends."""
    if value <= low:
        return 0.0
    if value >= high:
        return 100.0
    return (value - low) / (high - low) * 100


def composite_quality_score(roe_pct, de_value, icr_value, icr_label, cfo, pat):
    scores = []

    if roe_pct is not None:
        scores.append(_scale(roe_pct, 0, 40))

    if de_value is not None:
        # lower D/E is better, so scale is inverted: 0 -> 100, 3.0+ -> 0
        scores.append(100 - _scale(de_value, 0, 3.0))

    if icr_label == "Debt Free":
        scores.append(100.0)
    elif icr_value is not None:
        scores.append(_scale(icr_value, 1.5, 3.0))

    if cfo is not None and pat is not None and pat != 0:
        cfo_pat_ratio = cfo / pat
        scores.append(_scale(cfo_pat_ratio, 0, 1.0))

    if not scores:
        return None

    return sum(scores) / len(scores)