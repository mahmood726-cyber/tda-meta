import os
import shutil
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def tmp_path():
    base_dir = Path(__file__).resolve().parent / ".pytest_tmp_local"
    base_dir.mkdir(exist_ok=True)
    temp_dir = base_dir / f"pytest-{uuid.uuid4().hex}"
    temp_dir.mkdir()
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def pytest_collection_modifyitems(config, items):
    if os.environ.get("RUN_BROWSER_TESTS") == "1":
        return

    skip_browser = pytest.mark.skip(
        reason="Set RUN_BROWSER_TESTS=1 to run Selenium UI tests in a browser-capable environment."
    )
    for item in items:
        if "test_ui" in item.nodeid:
            item.add_marker(skip_browser)
