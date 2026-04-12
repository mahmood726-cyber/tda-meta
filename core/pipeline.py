import csv
import datetime
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.math import calculate_distance_matrix, simplified_persistent_homology

DATA_PATH = REPO_ROOT / "data" / "tda_results.json"
JS_DATA_PATH = REPO_ROOT / "data" / "tda_results.js"
RAW_DATA_CSV = REPO_ROOT / "data" / "raw_domains.csv"
METHODOLOGY = "E156 TDA (Persistent Homology) - [DML + Conformal + Reliability Shock]"


def _serialize_browser_bundle(payload):
    return f"window.__TDA_DATA__ = {json.dumps(payload, indent=2)};\n"


def load_raw_domains():
    """Ingest domains from CSV and extract all coordinate columns (c1, c2, ...)."""
    if RAW_DATA_CSV.exists():
        domains = []
        with RAW_DATA_CSV.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Dynamically collect all columns starting with 'c' followed by a digit
                coord_keys = sorted([k for k in row.keys() if k.startswith('c') and k[1:].isdigit()])
                domains.append({
                    "name": row["domain_name"],
                    "coords": [float(row[k]) for k in coord_keys],
                    "truth_cert": {
                        "locator": row.get("locator", "UNCERTIFIED"),
                        "hash": row.get("source_hash", "0x0000")
                    }
                })
        return domains
    
    # Legacy fallback (UNCERTIFIED)
    return [
        {"name": "USA_Cardio [SIM]", "coords": [95, 30, 100, 95, 30, 100, 1.0], "truth_cert": {"locator": "UNCERTIFIED", "hash": "0x00"}},
        {"name": "Somalia_Neglected_Trop [SIM]", "coords": [15, 85, 5, 15, 85, 5, 1.0], "truth_cert": {"locator": "UNCERTIFIED", "hash": "0x00"}}
    ]


def run_pipeline(output_path=None):
    domains = load_raw_domains()
    
    labels = [d["name"] for d in domains]
    coords = [d["coords"] for d in domains]
    
    dist_matrix = calculate_distance_matrix(coords)
    # Hardened 7D-DML Call (Reliability is in coords index 6)
    gaps, merges = simplified_persistent_homology(dist_matrix, labels, data_points=coords)
    
    # Map domain metadata back to gaps for TruthCert compliance
    domain_map = {d["name"]: d for d in domains}
    
    # Normalize isolation scores 0-100 for dashboard
    max_iso = max([g["isolation_score"] for g in gaps]) if gaps else 1
    for g in gaps:
        g["isolation_score_normalized"] = float((g["isolation_score"] / max_iso) * 100.0)
        # Attach TruthCert and Reliability
        domain_info = domain_map.get(g["domain"], {})
        g["truth_cert"] = domain_info.get("truth_cert", {"locator": "UNCERTIFIED", "hash": "0x00"})
        # C7 is reliability
        g["reliability_index"] = domain_info.get("coords", [1.0]*7)[6] if len(domain_info.get("coords", [])) >= 7 else 1.0
    
    destination = DATA_PATH if output_path is None else Path(output_path)
    js_destination = JS_DATA_PATH if output_path is None else destination.with_suffix(".js")
    destination.parent.mkdir(parents=True, exist_ok=True)
    js_destination.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "audit": {
            "methodology": METHODOLOGY,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "output_path": str(destination),
            "output_js_path": str(js_destination),
        },
        "domains": domains,
        "evidence_gaps": gaps,
        "merge_sequence": merges
    }

    with destination.open("w", encoding="utf-8") as handle:
        json.dump(output, handle, indent=2)
        handle.write("\n")

    with js_destination.open("w", encoding="utf-8") as handle:
        handle.write(_serialize_browser_bundle(output))

    return output

if __name__ == "__main__":
    run_pipeline()
    print("TDA-Meta pipeline complete. Evidence gaps identified.")
