"""
conftest.py
===========
Pytest fixtures that provide both runner modes.

Fixtures:
  fastapi_runner  — uses FastAPI TestClient (no server needed, for CI)
  http_runner     — uses requests against a real base URL
  runner          — alias, defaults to fastapi_runner;
                    switch to http_runner by setting env var API_MODE=http

The test files don't import the runner directly — pytest injects whichever
fixture they declare as a parameter.
"""

import os
import pytest
from test.api_test_runner import ApiTestRunner

# ---------------------------------------------------------------------------
# Attempt to import the FastAPI app.
# If this project only has a live URL (no local app), this import is skipped
# and only http_runner is available.
# ---------------------------------------------------------------------------
try:
    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app
    HAS_LOCAL_APP = True
except ImportError:
    HAS_LOCAL_APP = False


# ---------------------------------------------------------------------------
# Fixture: FastAPI TestClient runner
# Scope = "session" so the client is reused across all tests in the run.
# The store is cleared between test classes in the test files themselves.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def fastapi_runner():
    if not HAS_LOCAL_APP:
        pytest.skip("No local FastAPI app found — use http_runner instead")

    client = TestClient(fastapi_app)
    runner = ApiTestRunner(client=client)
    yield runner
    runner.clear()


# ---------------------------------------------------------------------------
# Fixture: requests-based runner pointing at a real URL
# Base URL is read from env var so it works for localhost, staging, or prod.
#
# Usage:
#   API_BASE_URL=http://localhost:8000 pytest
#   API_BASE_URL=https://staging.myapp.com pytest
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def http_runner():
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    # Optional: inject a bearer token from env for authenticated endpoints
    token = os.getenv("API_TOKEN", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    runner = ApiTestRunner(base_url=base_url, headers=headers)
    yield runner
    runner.clear()


# ---------------------------------------------------------------------------
# Fixture: `runner` — auto-selects mode based on env var API_MODE
#
# API_MODE=testclient  (default)  → fastapi_runner
# API_MODE=http                   → http_runner
#
# This lets you write tests that say `def test_x(runner)` and switch
# between local and real-server mode with a single env var.
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def runner(fastapi_runner, http_runner):
    mode = os.getenv("API_MODE", "testclient").lower()
    if mode == "http":
        return http_runner
    return fastapi_runner