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


def _load_required_json(path):
    if not path.exists():
        raise FileNotFoundError(f"Missing required input artifact: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def synthesize_aleph():
    tda = _load_required_json(TDA_RESULTS)
    shock = _load_required_json(SHOCK_RESULTS)

    tda_gap_map = {g["domain"]: g for g in tda["evidence_gaps"]}
    tda_domain_map = {d["name"]: d for d in tda["domains"]}
    shock_map = {r["treatment"]: r for r in shock["results"]}

    aleph_results = []
    all_domains = sorted(set(tda_domain_map.keys()) | set(shock_map.keys()))

    for domain in all_domains:
        if domain not in tda_domain_map:
            raise KeyError(f"Domain '{domain}' is missing from the TDA domain surface.")

        tda_data = tda_gap_map.get(domain, {})
        domain_metadata = tda_domain_map[domain]
        shock_data = shock_map.get(domain, {})

        coords = domain_metadata.get("coords", [])
        reliability = float(tda_data.get("reliability_index", coords[6] if len(coords) >= 7 else 1.0))
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
            "locator": domain_metadata["truth_cert"]["locator"],
        })

    aleph_results.sort(key=lambda x: (-x["aleph_score"], x["domain"]))

    output = {
        "audit": {
            "methodology": "Aleph Grand Unified Synthesis (v2026)",
            "timestamp": tda["audit"]["timestamp"],
            "components": ["Forensic-Reliability", "Topological-Integrity", "Quantum-Ranking"]
        },
        "results": aleph_results
    }

    with OUTPUT_ALEPH.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    with OUTPUT_ALEPH.with_suffix(".js").open("w", encoding="utf-8") as f:
        f.write(f"window.__ALEPH_DATA__ = {json.dumps(output, indent=2)};\n")

    print(f"Aleph Grand Unified Synthesis complete. Final scores saved to {OUTPUT_ALEPH}")

if __name__ == "__main__":
    synthesize_aleph()
