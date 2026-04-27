import json
import sys
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TDA_RESULTS = REPO_ROOT / "data" / "tda_results.json"
SHOCK_RESULTS = REPO_ROOT.parent / "nma-quantum-shock" / "data" / "shock_results.json"
OUTPUT_ALEPH = REPO_ROOT / "data" / "aleph_scores.json"

def synthesize_aleph():
    if not TDA_RESULTS.exists() or not SHOCK_RESULTS.exists():
        print(f"Error: Missing input artifacts.\nTDA: {TDA_RESULTS.exists()}\nSHOCK: {SHOCK_RESULTS.exists()}")
        return

    with TDA_RESULTS.open("r") as f:
        tda = json.load(f)
    
    with SHOCK_RESULTS.open("r") as f:
        shock = json.load(f)

    tda_map = {g["domain"]: g for g in tda["evidence_gaps"]}
    shock_map = {r["treatment"]: r for r in shock["results"]}

    aleph_results = []
    all_domains = set(tda_map.keys()) | set(shock_map.keys())

    for domain in all_domains:
        tda_data = tda_map.get(domain, {})
        shock_data = shock_map.get(domain, {})

        reliability = float(tda_data.get("reliability_index", 1.0))
        topological_integrity = 1.0 - (tda_data.get("isolation_score_normalized", 0.0) / 100.0)
        ranking_power = float(shock_data.get("sucra_shocked", 0.5))

        aleph_score = (0.4 * reliability) + (0.3 * topological_integrity) + (0.3 * ranking_power)
        
        status = "CERTIFIED" if aleph_score > 0.8 else ("SUSPICIOUS" if aleph_score > 0.5 else "CRITICAL")
        if "[SIM]" in domain: status = "SIMULATED"

        aleph_results.append({
            "domain": domain,
            "aleph_score": float(aleph_score * 100),
            "reliability_component": reliability,
            "topology_component": topological_integrity,
            "ranking_component": ranking_power,
            "certification": status,
            "locator": tda_data.get("truth_cert", {}).get("locator", "UNCERTIFIED")
        })

    aleph_results.sort(key=lambda x: x["aleph_score"], reverse=True)

    output = {
        "audit": {
            "methodology": "Aleph Grand Unified Synthesis (v2026)",
            "timestamp": tda["audit"]["timestamp"],
            "components": ["Forensic-Reliability", "Topological-Integrity", "Quantum-Ranking"]
        },
        "results": aleph_results
    }

    with OUTPUT_ALEPH.open("w") as f:
        json.dump(output, f, indent=2)
    
    with OUTPUT_ALEPH.with_suffix(".js").open("w") as f:
        f.write(f"window.__ALEPH_DATA__ = {json.dumps(output, indent=2)};\n")

    print(f"Aleph Grand Unified Synthesis complete. Final scores saved to {OUTPUT_ALEPH}")

if __name__ == "__main__":
    synthesize_aleph()
