"""Runs the JavaScript logic tests (js_tests/) as part of the Python test run.

They need Node.js. Where Node is not installed, this test is skipped.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

WEB_APP_DIR = Path(__file__).resolve().parent.parent
JS_TESTS_DIR = WEB_APP_DIR / "js_tests"


def test_the_javascript_logic_tests_pass():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed")

    # Node is given the test files themselves, not their folder. Given a folder, Node 22 and
    # Node 24 take it for one file and fail with "Cannot find module"; other versions accept
    # it. A list of files is understood by every version.
    test_files = sorted(str(path.relative_to(WEB_APP_DIR)) for path in JS_TESTS_DIR.glob("*.test.js"))
    assert test_files, "There are no JavaScript logic tests to run"

    result = subprocess.run(
        [node, "--test", *test_files], cwd=WEB_APP_DIR, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
