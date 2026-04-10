import numpy as np

def calculate_distance_matrix(data_points):
    """
    Computes pairwise Euclidean distances between clinical domains.
    Each domain is represented by its (Income, Disease Prevalence, Healthcare Access).
    """
    n = len(data_points)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            diff = np.array(data_points[i]) - np.array(data_points[j])
            dist_matrix[i, j] = np.sqrt(np.sum(diff**2))
    return dist_matrix

def simplified_persistent_homology(dist_matrix, labels):
    """
    Simulates 0-D persistent homology (clustering/connected components).
    Returns the 'birth' and 'death' of evidence clusters.
    """
    n = len(dist_matrix)
    # Track which component each node belongs to
    components = {i: [i] for i in range(n)}
    
    # Get all unique pairwise distances (edges)
    edges = []
    for i in range(n):
        for j in range(i+1, n):
            edges.append((dist_matrix[i, j], i, j))
            
    edges.sort(key=lambda x: x[0])
    
    births = {i: 0.0 for i in range(n)}
    deaths = {i: float('inf') for i in range(n)}
    merges = []
    
    for dist, i, j in edges:
        # Find roots
        comp_i = None
        comp_j = None
        for key, members in components.items():
            if i in members: comp_i = key
            if j in members: comp_j = key
            
        if comp_i != comp_j:
            # Merge components
            merges.append({
                "distance": float(dist),
                "merged": [labels[comp_i], labels[comp_j]]
            })
            
            # The smaller component 'dies', the larger one absorbs it
            if len(components[comp_i]) >= len(components[comp_j]):
                components[comp_i].extend(components[comp_j])
                deaths[comp_j] = dist
                del components[comp_j]
            else:
                components[comp_j].extend(components[comp_i])
                deaths[comp_i] = dist
                del components[comp_i]
                
    # The last remaining component never dies
    # Find the gaps (nodes with very late deaths = highly isolated evidence voids)
    gaps = []
    for i in range(n):
        persistence = deaths[i] - births[i]
        if persistence != float('inf'):
            gaps.append({
                "domain": labels[i],
                "birth": float(births[i]),
                "death": float(deaths[i]),
                "isolation_score": float(persistence)
            })
            
    # Sort by isolation score (largest evidence gaps first)
    gaps.sort(key=lambda x: x["isolation_score"], reverse=True)
    return gaps, merges
