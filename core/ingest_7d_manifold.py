import json
import pandas as pd
import hashlib
import csv
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_JSON = REPO_ROOT.parent / "raw_data.json"
RAW_TRIALS_CSV = REPO_ROOT.parent / "novel-nma-tournament" / "cardiology_trials_raw.csv"
OUTPUT_CSV = REPO_ROOT / "data" / "raw_domains.csv"

# Geographic Proxy Mapping (Reuse)
GEO_PROXIES = {
    "Japan": [92.0, 15.0, 98.0, "East Asia"],
    "Athens": [75.0, 25.0, 80.0, "Southern Europe"],
    "Greece": [75.0, 25.0, 80.0, "Southern Europe"],
    "Paris": [90.0, 20.0, 95.0, "Western Europe"],
    "Montpellier": [90.0, 20.0, 95.0, "Western Europe"],
    "France": [90.0, 20.0, 95.0, "Western Europe"],
    "Taiwan": [88.0, 18.0, 92.0, "East Asia"],
    "Hospital Universitario La Paz": [85.0, 22.0, 88.0, "Southern Europe"],
    "Spain": [85.0, 22.0, 88.0, "Southern Europe"],
    "Apple Inc": [95.0, 30.0, 100.0, "North America"],
    "USA": [95.0, 30.0, 100.0, "North America"]
}

DEFAULT_GEO = [80.0, 25.0, 85.0, "Global/Undefined"]

def extract_clinical_coords(baseline_measures):
    """Extracts [Mean Age, % Female, Sample Size]."""
    coords = [None, None, None] 
    for measure in baseline_measures:
        title = measure.get("title", "").lower()
        if "age" in title and "continuous" in title:
            try:
                categories = measure.get("classes", [{}])[0].get("categories", [{}])[0]
                measurements = categories.get("measurements", [])
                coords[0] = float(measurements[-1].get("value", 65.0))
            except: pass
        if "sex" in title and "female" in title:
            try:
                categories = measure.get("classes", [{}])[0].get("categories", [])
                for cat in categories:
                    if "female" in cat.get("title", "").lower():
                        measurements = cat.get("measurements", [])
                        coords[1] = float(measurements[-1].get("value", 0.0))
            except: pass
        if "total" in title and "participants" in title:
             try:
                categories = measure.get("classes", [{}])[0].get("categories", [{}])[0]
                measurements = categories.get("measurements", [])
                coords[2] = float(measurements[-1].get("value", 100.0))
             except: pass

    if coords[0] is None: coords[0] = 65.0
    if coords[1] is None: coords[1] = 0.0
    if coords[2] is None: coords[2] = 100.0
    if coords[1] > 1.0: coords[1] = (coords[1] / coords[2]) * 100.0
    return coords

def ingest_7d_manifold():
    # 1. Load Clinical Data
    clinical_map = {}
    if RAW_DATA_JSON.exists():
        with RAW_DATA_JSON.open("r", encoding="utf-8") as f:
            data = json.load(f)
            for trial in data.get("reported", []):
                nct_id = trial.get("nct_id")
                clinical_map[nct_id] = extract_clinical_coords(trial.get("baseline", []))

    # 2. Load Geo Data
    geo_map = {}
    if RAW_TRIALS_CSV.exists():
        with RAW_TRIALS_CSV.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                nct_id = row['nct_id']
                sponsor_title = (row['sponsor'] + " " + row['title']).lower()
                coords = DEFAULT_GEO
                for key, val in GEO_PROXIES.items():
                    if key.lower() in sponsor_title:
                        coords = val
                        break
                geo_map[nct_id] = coords

    # 3. Merge into 7D Space
    all_ncts = set(clinical_map.keys()) | set(geo_map.keys())
    new_rows = []
    
    # RETRACTION SHOCK LIST
    RETRACTED_NCTS = {
        "NCT04509674": 0.0, # Primary Retraction (Simulated failure)
        "NCT00299572": 0.6  # Collateral Damage (Secondary shock)
    }
    
    for nct_id in all_ncts:
        clinical = clinical_map.get(nct_id, [65.0, 50.0, 100.0])
        geo = geo_map.get(nct_id, [80.0, 25.0, 85.0, "Global/Undefined"])
        reliability = RETRACTED_NCTS.get(nct_id, 1.0)
        
        # 7D Vector: [Age, %Female, N, SES, Prev, Infra, Reliability]
        full_coords = clinical + geo[:3] + [reliability]
        
        content_hash = hashlib.sha256(f"{nct_id}-7d-manifold".encode()).hexdigest()[:8]
        new_rows.append({
            "domain_name": f"{nct_id} ({geo[3]})",
            "c1": full_coords[0], "c2": full_coords[1], "c3": full_coords[2],
            "c4": full_coords[3], "c5": full_coords[4], "c6": full_coords[5],
            "c7": full_coords[6], # Reliability Index
            "locator": f"AACT-7D-{nct_id}",
            "source_hash": content_hash
        })

    # Add 7D Voids
    new_rows.append({"domain_name": "Somalia_Pediatric_NTD [SIM]", "c1": 8.0, "c2": 50.0, "c3": 50.0, "c4": 15.0, "c5": 85.0, "c6": 5.0, "c7": 1.0, "locator": "WHO-NTD-7D", "source_hash": "f5g6h7i8"})
    
    out_df = pd.DataFrame(new_rows)
    out_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Successfully merged {len(new_rows)} domains into 7D manifold with reliability shocks.")

if __name__ == "__main__":
    ingest_7d_manifold()
