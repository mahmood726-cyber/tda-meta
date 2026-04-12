from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_index_uses_local_assets_only():
    content = (REPO_ROOT / "index.html").read_text(encoding="utf-8")
    assert "cdn.jsdelivr.net" not in content
    assert 'src="data/tda_results.js"' in content


def test_app_uses_embedded_payload_and_local_chart_markup():
    content = (REPO_ROOT / "app.js").read_text(encoding="utf-8")
    assert "getEmbeddedPayload" in content
    assert "__TDA_DATA__" in content
    assert "new Chart(" not in content
