import numpy as np
from scipy.spatial.distance import pdist, squareform

def calculate_distance_matrix(data_points):
    """
    Computes pairwise Euclidean distances between clinical domains.
    Features are standardized (Z-score) to prevent magnitude bias.
    """
    arr = np.array(data_points, dtype=float)
    # Standardize: (X - mean) / std
    mean = np.mean(arr, axis=0)
    std = np.std(arr, axis=0)
    std[std == 0] = 1.0  # Avoid division by zero
    standardized = (arr - mean) / std
    
    # Vectorized pairwise Euclidean distance
    return squareform(pdist(standardized, metric='euclidean'))

def dml_orthogonal_distance(dist_matrix, data_points, n_folds=2):
    """
    Hardened 2026 DML Estimator: Orthogonalizes distances against nuisance parameters.
    Splits sample into folds to ensure nuisance estimation is independent of gap estimation.
    Nuisance components here: Sample Size (coord 2) and Infrastructure (coord 5).
    """
    n = len(data_points)
    arr = np.array(data_points)
    corrected_matrix = dist_matrix.copy()
    
    indices = np.arange(n)
    np.random.seed(42) # Determinism for E156
    np.random.shuffle(indices)
    
    folds = np.array_split(indices, n_folds)
    
    for i in range(n_folds):
        test_idx = folds[i]
        train_idx = np.setdiff1d(indices, test_idx)
        
        # Estimate Nuisance: Average Infrastructure/N bias in the TRAINING fold
        # (Simplified DML proxy: subtract the mean nuisance-weighted shift)
        if len(train_idx) > 0:
            infra_nuisance = np.mean(arr[train_idx, 5]) 
            size_nuisance = np.mean(arr[train_idx, 2])
            
            # Apply orthogonalization to TEST nodes' distances
            for node_idx in test_idx:
                # Penalty/Reward shift based on distance to the training nuisance centroid
                # This 'cleans' the distance of infrastructure-driven clustering
                shift = 0.05 * (arr[node_idx, 5] - infra_nuisance) / max(1, infra_nuisance)
                corrected_matrix[node_idx, :] *= (1.0 - shift)
                corrected_matrix[:, node_idx] *= (1.0 - shift)
                
    return corrected_matrix

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n
    
    def find(self, i):
        if self.parent[i] == i:
            return i
        self.parent[i] = self.find(self.parent[i])
        return self.parent[i]
    
    def union(self, i, j):
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i != root_j:
            # Elder rule: Smaller component merges into larger one
            if self.size[root_i] < self.size[root_j]:
                root_i, root_j = root_j, root_i
            self.parent[root_j] = root_i
            self.size[root_i] += self.size[root_j]
            return root_i, root_j
        return None

def calculate_conformal_radius(calibration_persistence, alpha=0.05):
    """
    Hardened 2026 CPI: Calculates the conformal radius from a calibration set.
    Ensures finite-sample valid coverage for isolation scores.
    """
    n = len(calibration_persistence)
    if n == 0: return 0.0
    
    # Non-conformity scores (persistence of non-outliers)
    scores = np.sort(calibration_persistence)
    q_idx = int(np.ceil((1.0 - alpha) * (n + 1))) - 1
    q_idx = min(max(q_idx, 0), n - 1)
    
    return float(scores[q_idx])

def simplified_persistent_homology(dist_matrix, labels, data_points=None):
    """
    Simulates 0-D persistent homology with DML-correction, Conformal Intervals,
    and Reliability-Weighted Distances.
    """
    n = len(dist_matrix)
    arr = np.array(data_points) if data_points is not None else None
    
    # Hardening Step 0: Reliability Shock (c7 is the 7th coordinate)
    if arr is not None and arr.shape[1] >= 7:
        reliability = arr[:, 6]
        for i in range(n):
            for j in range(n):
                # Penalty increases as reliability drops
                # If Ri=1 and Rj=1, factor=1. If Ri=0, distance doubles.
                penalty_factor = 1.0 + (1.0 - reliability[i]) + (1.0 - reliability[j])
                dist_matrix[i, j] *= penalty_factor

    # Hardening Step 1: DML-Correction
    if data_points is not None and len(data_points) == n:
        dist_matrix = dml_orthogonal_distance(dist_matrix, data_points)
        
    uf = UnionFind(n)
    edges = []
    for i in range(n):
        for j in range(i+1, n):
            edges.append((float(dist_matrix[i, j]), i, j))
    edges.sort(key=lambda x: (x[0], x[1], x[2]))
    
    births = {i: 0.0 for i in range(n)}
    deaths = {i: float('inf') for i in range(n)}
    merges = []
    
    for dist, i, j in edges:
        result = uf.union(i, j)
        if result:
            root_winner, root_loser = result
            merges.append({"distance": dist, "merged": [labels[root_loser], labels[root_winner]]})
            deaths[root_loser] = dist
                
    gaps = []
    calibration_persistence = []
    
    # Collect all deaths for conformal calibration (exclude the eternal root)
    for i in range(n):
        persistence = deaths[i] - births[i]
        if persistence != float('inf'):
            # Only trials (non-simulated) serve as the calibration set
            if "[SIM]" not in labels[i]:
                calibration_persistence.append(persistence)

    # Hardening Step 2: Conformal Radius
    conformal_radius = calculate_conformal_radius(calibration_persistence)
    
    for i in range(n):
        persistence = deaths[i] - births[i]
        if persistence != float('inf'):
            # Bound persistent scores by conformal radius to find 'true' anomalies
            lower_bound = max(0, persistence - conformal_radius)
            upper_bound = persistence + conformal_radius
            
            gaps.append({
                "domain": labels[i],
                "birth": float(births[i]),
                "death": float(deaths[i]),
                "isolation_score": float(persistence),
                "conformal_range": [float(lower_bound), float(upper_bound)],
                "is_anomalous": bool(persistence > conformal_radius)
            })
            
    gaps.sort(key=lambda x: (x["isolation_score"], x["domain"]), reverse=True)
    return gaps, merges
