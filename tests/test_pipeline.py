import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core import pipeline


def test_run_pipeline_writes_json_and_js(tmp_path):
    destination = tmp_path / "tda_results.json"
    payload = pipeline.run_pipeline(output_path=destination)

    assert destination.exists()
    assert destination.with_suffix(".js").exists()
    assert payload["audit"]["output_path"] == pipeline._audit_path(destination)
    assert payload["audit"]["output_js_path"] == pipeline._audit_path(destination.with_suffix(".js"))
    assert "__TDA_DATA__" in destination.with_suffix(".js").read_text(encoding="utf-8")

    persisted = json.loads(destination.read_text(encoding="utf-8"))
    assert len(persisted["domains"]) >= 1
    assert len(persisted["evidence_gaps"]) >= 1


def test_load_raw_domains_fails_closed_without_csv(monkeypatch, tmp_path):
    monkeypatch.delenv("TDA_RAW_DOMAINS", raising=False)
    monkeypatch.setattr(pipeline, "RAW_DATA_CSV", tmp_path / "missing_raw_domains.csv")

    with pytest.raises(FileNotFoundError, match="Missing required TDA raw domains CSV"):
        pipeline.load_raw_domains()


def test_load_raw_domains_rejects_missing_truth_cert_fields(monkeypatch, tmp_path):
    raw_csv = tmp_path / "raw_domains.csv"
    raw_csv.write_text(
        "domain_name,c1,c2,c3,c4,c5,c6,c7,locator,source_hash\n"
        "Domain A,1,2,3,4,5,6,7,,hash-1\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(pipeline, "RAW_DATA_CSV", raw_csv)

    with pytest.raises(ValueError, match="missing required truth-cert fields"):
        pipeline.load_raw_domains()
