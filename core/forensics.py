import numpy as np
import collections

def benford_score(data_series):
    """
    Computes a reliability score based on Benford's Law (Leading Digit Distribution).
    Returns a score from 0.0 (likely fake) to 1.0 (perfect fit).
    """
    digits = []
    for x in data_series:
        try:
            s = str(abs(float(x))).replace('0.', '').replace('.', '').lstrip('0')
            if s:
                digits.append(int(s[0]))
        except (ValueError, TypeError):
            continue
            
    if len(digits) < 10:
        return 1.0
        
    counts = collections.Counter(digits)
    observed = np.array([counts.get(i, 0) for i in range(1, 10)]) / len(digits)
    expected = np.log10(1 + 1/np.arange(1, 10))
    mad = np.mean(np.abs(observed - expected))
    reliability = 1.0 - (mad / 0.05)
    return float(max(0.0, min(1.0, reliability)))

def grim_test(mean, n, items=1):
    """GRIM test for mathematical consistency of means."""
    try:
        n = int(n)
        mean = float(mean)
        if n <= 0: return True
        total_sum = mean * n * items
        rounded_sum = round(total_sum)
        error = abs(total_sum - rounded_sum)
        return error < 0.51
    except (TypeError, ValueError):
        return True

def calculate_forensic_reliability(age_series, n_series):
    """Combines Benford and GRIM into a single reliability index."""
    b_score = benford_score(n_series)
    grim_failures = 0
    valid_tests = 0
    for age, n in zip(age_series, n_series):
        if not grim_test(age, n):
            grim_failures += 1
        valid_tests += 1
    g_score = 1.0 - (grim_failures / max(1, valid_tests))
    return float(0.4 * b_score + 0.6 * g_score)
