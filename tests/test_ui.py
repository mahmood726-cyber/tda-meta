import sys
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from threading import Thread

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from browser_rotator import get_driver

PREFERRED_PORT = 8000


class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).resolve().parent.parent), **kwargs)

    def log_message(self, format, *args):
        pass


@pytest.fixture(scope="module")
def base_url():
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PREFERRED_PORT), QuietHandler)
    except OSError:
        server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        port = server.server_address[1]
        yield f"http://127.0.0.1:{port}/index.html"
    finally:
        server.shutdown()
        server.server_close()


def test_tda_ui_integrity(base_url):
    driver = get_driver()
    try:
        driver.get(base_url)
        wait = WebDriverWait(driver, 20)
        wait.until(lambda d: d.find_elements(By.CLASS_NAME, "bar-row"))

        rows = driver.find_elements(By.CLASS_NAME, "bar-row")
        assert rows, "No evidence gaps rendered in chart"

        domain_count = int(driver.find_element(By.ID, "domainCount").text)
        assert domain_count > 0, "Domain count metric is zero"

        certs = driver.find_elements(By.CLASS_NAME, "truth-cert")
        assert certs, "TruthCert information missing from gap cards"
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
