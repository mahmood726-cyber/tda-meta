import csv
import datetime
import json
import os
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


def _audit_path(path):
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def resolve_raw_domains_csv():
    override = os.environ.get("TDA_RAW_DOMAINS")
    candidates = []
    if override:
        candidates.append(Path(override))
    candidates.append(RAW_DATA_CSV)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    checked = "\n - ".join(str(candidate) for candidate in candidates)
    raise FileNotFoundError(f"Missing required TDA raw domains CSV. Checked:\n - {checked}")


def _required_truth_cert(row):
    locator = (row.get("locator") or "").strip()
    source_hash = (row.get("source_hash") or "").strip()
    domain_name = row.get("domain_name", "<unknown domain>")

    if not locator or not source_hash:
        raise ValueError(
            f"Domain '{domain_name}' is missing required truth-cert fields "
            f"(locator/source_hash) in the raw domains CSV."
        )

    return {"locator": locator, "hash": source_hash}


def load_raw_domains():
    """Ingest domains from CSV and extract all coordinate columns (c1, c2, ...)."""
    raw_data_csv = resolve_raw_domains_csv()
    domains = []
    with raw_data_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Dynamically collect all columns starting with 'c' followed by a digit
            coord_keys = sorted([k for k in row.keys() if k.startswith('c') and k[1:].isdigit()])
            truth_cert = _required_truth_cert(row)
            domains.append({
                "name": row["domain_name"],
                "coords": [float(row[k]) for k in coord_keys],
                "truth_cert": truth_cert,
            })
    return domains


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
        if g["domain"] not in domain_map:
            raise KeyError(f"Evidence gap domain '{g['domain']}' is missing from the loaded raw domains surface.")
        domain_info = domain_map[g["domain"]]
        g["truth_cert"] = domain_info["truth_cert"]
        # C7 is reliability
        coords = domain_info.get("coords", [])
        g["reliability_index"] = coords[6] if len(coords) >= 7 else 1.0
    
    destination = DATA_PATH if output_path is None else Path(output_path)
    js_destination = JS_DATA_PATH if output_path is None else destination.with_suffix(".js")
    destination.parent.mkdir(parents=True, exist_ok=True)
    js_destination.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "audit": {
            "methodology": METHODOLOGY,
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "output_path": _audit_path(destination),
            "output_js_path": _audit_path(js_destination),
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
