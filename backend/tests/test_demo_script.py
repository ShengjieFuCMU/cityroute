# backend/tests/test_demo_script.py
import os
import pytest

skip = pytest.mark.skipif(os.getenv("RUN_DEMO_SMOKE") != "1", reason="demo smoke disabled")


@skip
def test_demo_script_imports_and_main():
    # basic import sanity and main callable existence
    import scripts.demo_run as demo
    assert callable(getattr(demo, "main", None))
    # Intentionally not running main() to avoid needing a live server in CI.

