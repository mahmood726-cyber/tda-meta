import json
import numpy as np
import datetime
import os

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.math import calculate_distance_matrix, simplified_persistent_homology

def run_pipeline():
    # Simulated Medical Domains in a 3D Evidence Space
    # Dimensions: [Socioeconomic Index, Disease Prevalence, Trial Infrastructure]
    domains = [
        {"name": "USA_Cardio", "coords": [95, 30, 100]},
        {"name": "UK_Cardio", "coords": [90, 28, 95]},
        {"name": "EU_Diabetes", "coords": [88, 25, 90]},
        {"name": "USA_Diabetes", "coords": [93, 27, 98]},
        
        # Moderately isolated domains
        {"name": "Brazil_Cardio", "coords": [65, 40, 60]},
        {"name": "China_Diabetes", "coords": [70, 35, 75]},
        
        # High isolation (Evidence Gaps)
        {"name": "Nigeria_Maternal", "coords": [35, 60, 20]},
        {"name": "Kenya_Malaria", "coords": [40, 70, 25]},
        {"name": "India_Rural_Diabetes", "coords": [45, 55, 30]},
        
        # Extreme Void
        {"name": "Somalia_Neglected_Trop", "coords": [15, 85, 5]}
    ]
    
    labels = [d["name"] for d in domains]
    coords = [d["coords"] for d in domains]
    
    dist_matrix = calculate_distance_matrix(coords)
    gaps, merges = simplified_persistent_homology(dist_matrix, labels)
    
    # Normalize isolation scores 0-100 for dashboard
    max_iso = max([g["isolation_score"] for g in gaps]) if gaps else 1
    for g in gaps:
        g["isolation_score_normalized"] = float((g["isolation_score"] / max_iso) * 100.0)
    
    output = {
        "audit": {
            "methodology": "E156 TDA (Persistent Homology for Evidence Voids)",
            "timestamp": datetime.datetime.now().isoformat()
        },
        "domains": domains,
        "evidence_gaps": gaps,
        "merge_sequence": merges
    }
    
    with open('data/tda_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("TDA-Meta pipeline complete. Evidence gaps identified.")

if __name__ == "__main__":
    run_pipeline()
