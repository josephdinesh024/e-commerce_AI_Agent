"""
test_api.py
===========
Test file — uses ApiTestRunner + structured ApiCase definitions.

Three test classes, each independent:
  TestItemsFlow       — sequential tests that share state (extract → reuse)
  TestAuthFlow        — login → token → authenticated calls
  TestValidation      — edge cases, error responses (no shared state)

Key pattern:
  Every test method receives `runner` (injected by pytest from conftest.py).
  The runner's store persists within a class because we use the same runner
  instance. Between classes we call runner.clear() in setup_method.

Run modes:
  pytest                                    # TestClient (default)
  API_MODE=http API_BASE_URL=http://localhost:8000 pytest   # real server
  API_MODE=http API_BASE_URL=https://staging.myapp.com pytest
"""

import pytest
from test.test_cases import (
    ITEMS_TEST_CASES,
    AUTH_TEST_CASES,
    VALIDATION_TEST_CASES,
    ApiCase,
)


def case_id(case):
    """Return a readable ID for pytest parametrized ApiCase objects."""
    return getattr(case, "id", str(case))


# =============================================================================
# Helpers
# =============================================================================

def run_case(runner, case: ApiCase):
    """
    Execute one ApiCase against the runner.

    Steps:
      1. Skip if case.skip is True
      2. Send the HTTP request  (endpoint placeholders resolved inside runner)
      3. Assert status + body
      4. Extract values into runner.store if case.extract is defined
    """
    if case.skip:
        pytest.skip(f"Skipped: {case.id}")

    response = runner.request(
        method   = case.method,
        endpoint = case.endpoint,
        body     = case.body,
        params   = case.params,
    )

    runner.assert_response(
        response,
        expected_status = case.expected_status,
        expected_body   = case.expected_body,
        contains        = case.contains,
    )

    if case.extract:
        runner.extract_many(response, case.extract)
        print(f"\n  [{case.id}] Stored: { {k: runner.store[k] for k in case.extract} }")

    return response


# =============================================================================
# Class 1 — Items flow (sequential, shared state via runner.store)
# =============================================================================

class TestItemsFlow:
    """
    Tests that run in order and share extracted values.

    Test order inside a class is preserved by pytest (top to bottom).
    Each test builds on state stored by the previous one.

      test_01 → health check (no state)
      test_02 → list items, extract item_id + item_name
      test_03 → get item by extracted item_id
      test_04 → create item, extract new_item_id
      test_05 → update item using new_item_id
      test_06 → delete item using new_item_id
      test_07 → confirm deleted item returns 404
    """

    def setup_method(self, method):
        """Called before each test method. Reset store for a clean flow."""
        pass   # intentionally not clearing — this class is sequential

    # ------------------------------------------------------------------
    # Parametrize with test case IDs for clear output in terminal
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("case", ITEMS_TEST_CASES, ids=case_id)
    def test_items_flow(self, runner, case):
        """
        Runs each ITEMS_TEST_CASES entry in order.
        pytest.mark.parametrize preserves list order, so state flows correctly.
        """
        run_case(runner, case)


# =============================================================================
# Class 2 — Auth flow (login → store token → use token)
# =============================================================================

class TestAuthFlow:
    """
    Login, extract token, use token in subsequent calls.

    Note: the auth token is stored in runner.store["auth_token"] after login.
    For endpoints that need it, pass it as a header directly:
        runner.request(..., headers={"Authorization": f"Bearer {runner.get('auth_token')}"})
    Or set it as a default header on the runner after extraction.
    """

    def setup_method(self, method):
        pass   # auth flow is also sequential — don't clear between steps

    @pytest.mark.parametrize("case", AUTH_TEST_CASES, ids=case_id)
    def test_auth_flow(self, runner, case):
        """Login → extract token → use token in next requests."""
        run_case(runner, case)


# =============================================================================
# Class 3 — Validation / edge cases (independent, no shared state)
# =============================================================================

class TestValidation:
    """
    Each case is independent — no state flows between them.
    We clear the store in setup so previous test classes don't bleed in.
    """

    def setup_method(self, method):
        pass   # each validation case is self-contained, no setup needed

    @pytest.mark.parametrize("case", VALIDATION_TEST_CASES, ids=case_id)
    def test_validation_cases(self, runner, case):
        run_case(runner, case)


# =============================================================================
# Direct / one-off tests — without parametrize
# These show how to use the runner and runner.store directly in a test body.
# =============================================================================

# class TestDirectUsage:
#     """
#     Shows how to write individual tests using the runner directly —
#     useful when a test needs custom logic beyond what ApiCase covers.
#     """

#     def setup_method(self, method):
#         pass

#     def test_create_and_immediately_fetch(self, runner):
#         """
#         Create a product, then immediately GET it using the extracted id.
#         Demonstrates using runner.store and runner.get() directly.
#         """
#         # Step 1 — create
#         create_res = runner.request(
#             method   = "post",
#             endpoint = "/products",
#             body     = {
#                 "name": "Direct Test Product",
#                 "description": "A direct test dress",
#                 "price": 15.00,
#                 "stock": 5,
#                 "image_url": "https://example.com/direct-test.jpg",
#             },
#         )
#         runner.assert_response(create_res, expected_status=201)

#         # Step 2 — extract and store the new id manually
#         product_id = runner.extract(create_res, ["id"])
#         runner.set("direct_product_id", product_id)

#         # Step 3 — fetch using stored id
#         get_res = runner.request("get", "/products/{direct_product_id}")
#         runner.assert_response(get_res, contains={"name": "Direct Test Product"})

#         # Step 4 — verify the name matches what we created
#         fetched_name = runner.extract(get_res, ["name"])
#         assert fetched_name == "Direct Test Product"

#     def test_pagination_query_params(self, runner):
#         """
#         Verify pagination params are passed correctly and response is valid.
#         Uses params= to send query string values.
#         """
#         res = runner.request(
#             method   = "get",
#             endpoint = "/products",
#             params   = {"skip": 0, "limit": 2},
#         )
#         runner.assert_response(res, expected_status=200)

#         body = res.json()
#         assert isinstance(body, list)

#     def test_search_with_query_param(self, runner):
#         """
#         Query params are accepted by the products endpoint.
#         """
#         res = runner.request(
#             method   = "get",
#             endpoint = "/products",
#             params   = {"limit": 1},
#         )
#         runner.assert_response(res, expected_status=200)

#     def test_post_with_body_placeholder(self, runner):
#         """
#         Demonstrates body placeholder resolution.
#         Uses a stored placeholder in the product name.
#         """
#         runner.set("direct_product_name", "Placeholder Dress")

#         res = runner.request(
#             method   = "post",
#             endpoint = "/products",
#             body     = {
#                 "name":        "{direct_product_name}",
#                 "description": "Created using placeholder resolution",
#                 "price":       12.50,
#                 "stock":       3,
#                 "image_url":   "https://example.com/placeholder.jpg",
#             },
#         )
#         runner.assert_response(res, expected_status=201)


