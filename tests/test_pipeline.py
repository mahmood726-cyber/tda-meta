import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core import pipeline


def test_run_pipeline_writes_json_and_js(tmp_path):
    destination = tmp_path / "tda_results.json"
    payload = pipeline.run_pipeline(output_path=destination)

    assert destination.exists()
    assert destination.with_suffix(".js").exists()
    assert payload["audit"]["output_path"] == str(destination)
    assert payload["audit"]["output_js_path"] == str(destination.with_suffix(".js"))
    assert "__TDA_DATA__" in destination.with_suffix(".js").read_text(encoding="utf-8")

    persisted = json.loads(destination.read_text(encoding="utf-8"))
    assert len(persisted["domains"]) >= 1
    assert len(persisted["evidence_gaps"]) >= 1
