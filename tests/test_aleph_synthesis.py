import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core import aleph_synthesis


def test_synthesize_aleph_uses_domain_truth_cert_when_gap_map_is_sparse(monkeypatch, tmp_path):
    tda_path = tmp_path / "tda_results.json"
    shock_path = tmp_path / "shock_results.json"
    output_path = tmp_path / "aleph_scores.json"

    tda_payload = {
        "audit": {"timestamp": "2026-04-29T00:00:00+00:00"},
        "domains": [
            {
                "name": "Domain A",
                "coords": [1, 2, 3, 4, 5, 6, 0.8],
                "truth_cert": {"locator": "AACT-7D-DomainA", "hash": "hash-a"},
            }
        ],
        "evidence_gaps": [],
    }
    shock_payload = {"results": [{"treatment": "Domain A", "sucra_shocked": 0.75}]}

    tda_path.write_text(json.dumps(tda_payload), encoding="utf-8")
    shock_path.write_text(json.dumps(shock_payload), encoding="utf-8")
    monkeypatch.setattr(aleph_synthesis, "TDA_RESULTS", tda_path)
    monkeypatch.setattr(aleph_synthesis, "SHOCK_RESULTS", shock_path)
    monkeypatch.setattr(aleph_synthesis, "OUTPUT_ALEPH", output_path)

    aleph_synthesis.synthesize_aleph()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["results"][0]["locator"] == "AACT-7D-DomainA"
    assert payload["results"][0]["reliability_component"] == 0.8


def test_synthesize_aleph_fails_closed_when_domain_metadata_missing(monkeypatch, tmp_path):
    tda_path = tmp_path / "tda_results.json"
    shock_path = tmp_path / "shock_results.json"

    tda_path.write_text(json.dumps({"audit": {"timestamp": "x"}, "domains": [], "evidence_gaps": []}), encoding="utf-8")
    shock_path.write_text(json.dumps({"results": [{"treatment": "Missing Domain", "sucra_shocked": 0.4}]}), encoding="utf-8")
    monkeypatch.setattr(aleph_synthesis, "TDA_RESULTS", tda_path)
    monkeypatch.setattr(aleph_synthesis, "SHOCK_RESULTS", shock_path)

    with pytest.raises(KeyError, match="Missing Domain"):
        aleph_synthesis.synthesize_aleph()


def test_synthesize_aleph_sorts_tied_scores_deterministically(monkeypatch, tmp_path):
    tda_path = tmp_path / "tda_results.json"
    shock_path = tmp_path / "shock_results.json"
    output_path = tmp_path / "aleph_scores.json"

    tda_payload = {
        "audit": {"timestamp": "2026-04-29T00:00:00+00:00"},
        "domains": [
            {"name": "Domain B", "coords": [1, 2, 3, 4, 5, 6, 1.0], "truth_cert": {"locator": "B", "hash": "b"}},
            {"name": "Domain A", "coords": [1, 2, 3, 4, 5, 6, 1.0], "truth_cert": {"locator": "A", "hash": "a"}},
        ],
        "evidence_gaps": [],
    }
    shock_payload = {
        "results": [
            {"treatment": "Domain B", "sucra_shocked": 0.0},
            {"treatment": "Domain A", "sucra_shocked": 0.0},
        ]
    }

    tda_path.write_text(json.dumps(tda_payload), encoding="utf-8")
    shock_path.write_text(json.dumps(shock_payload), encoding="utf-8")
    monkeypatch.setattr(aleph_synthesis, "TDA_RESULTS", tda_path)
    monkeypatch.setattr(aleph_synthesis, "SHOCK_RESULTS", shock_path)
    monkeypatch.setattr(aleph_synthesis, "OUTPUT_ALEPH", output_path)

    aleph_synthesis.synthesize_aleph()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert [row["domain"] for row in payload["results"]] == ["Domain A", "Domain B"]
