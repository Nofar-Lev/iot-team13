"""Runs the JavaScript logic tests (js_tests/) as part of the Python test run.

They need Node.js. Where Node is not installed, this test is skipped.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

WEB_APP_DIR = Path(__file__).resolve().parent.parent


def test_the_javascript_logic_tests_pass():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")
    result = subprocess.run(
        [node, "--test", "js_tests/"], cwd=WEB_APP_DIR, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
