import numpy as np
import collections

def benford_score(data_series):
    """
    Computes a reliability score based on Benford's Law (Leading Digit Distribution).
    Returns a score from 0.0 (likely fake) to 1.0 (perfect fit).
    """
    # Filter for positive numbers and extract leading digit
    digits = []
    for x in data_series:
        try:
            s = str(abs(float(x))).replace('0.', '').replace('.', '').lstrip('0')
            if s:
                digits.append(int(s[0]))
        except (ValueError, TypeError):
            continue
            
    if len(digits) < 10:
        return 1.0 # Insufficient data to penalize
        
    # Observed distribution
    counts = collections.Counter(digits)
    observed = np.array([counts.get(i, 0) for i in range(1, 10)]) / len(digits)
    
    # Expected Benford distribution: P(d) = log10(1 + 1/d)
    expected = np.log10(1 + 1/np.arange(1, 10))
    
    # Chi-square style distance (normalized to 0-1)
    # We use Mean Absolute Deviation (MAD) as it's more robust for small N
    mad = np.mean(np.abs(observed - expected))
    
    # MAD thresholds (classic forensics): 
    # < 0.006 (Close), 0.006-0.012 (Acceptable), > 0.015 (Suspicious)
    # Scaled to a reliability index
    reliability = 1.0 - (mad / 0.05) # Severe penalty for high MAD
    return float(max(0.0, min(1.0, reliability)))

def grim_test(mean, n, items=1):
    """
    GRIM (Granularity Related Error of Means) test.
    Checks if a reported mean is mathematically possible given the sample size.
    Only works for integers/counts (e.g., Age in years if rounded).
    """
    try:
        n = int(n)
        mean = float(mean)
        if n <= 0: return True
        
        # Possible sums are integers
        # sum = mean * n. If mean is reported to 1 decimal place, 
        # the underlying sum must be an integer.
        # We check if any integer in the range [sum - 0.5, sum + 0.5] exists.
        total_sum = mean * n * items
        rounded_sum = round(total_sum)
        error = abs(total_sum - rounded_sum)
        
        # Threshold depends on reporting precision (usually 0.5/n)
        # If mean is 65.4, reported to 1 decimal, the real mean is [65.35, 65.45]
        # So sum is in [n*65.35, n*65.45].
        return error < 0.51
    except:
        return True # Fail-open if data is malformed

def calculate_forensic_reliability(age_series, n_series):
    """
    Combines Benford and GRIM into a single reliability index.
    """
    # 1. Benford on N (Sample sizes usually follow Benford)
    b_score = benford_score(n_series)
    
    # 2. GRIM on Age
    grim_failures = 0
    valid_tests = 0
    for age, n in zip(age_series, n_series):
        if not grim_test(age, n):
            grim_failures += 1
        valid_tests += 1
    
    g_score = 1.0 - (grim_failures / max(1, valid_tests))
    
    # Composite Score (Weighted)
    return float(0.4 * b_score + 0.6 * g_score)
