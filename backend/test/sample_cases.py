"""
test_cases.py
=============
ApiCase definitions for the API test suite.

Renamed TestCase → ApiCase to avoid the pytest collection warning:
    "cannot collect test class 'TestCase' because it has __init__ constructor"

Pytest scans all files for classes starting with "Test" and tries to collect
them as test classes. Since our dataclass is named TestCase, pytest gets
confused. ApiCase has no such problem.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ApiCase:
    """
    One API test case.

    id              : human-readable name shown in pytest output
    method          : "get" | "post" | "put" | "patch" | "delete"
    endpoint        : path with optional {placeholders} resolved from store
    body            : JSON request body for POST/PUT/PATCH
    params          : URL query parameters  e.g. {"page": 1, "limit": 10}
    expected_status : expected HTTP status code (default 200)
    expected_body   : full exact match of response JSON
    contains        : partial response check — only these key/values must match
    extract         : extract values into store after the call
                      format: { "store_key": ["path", 0, "to", "value"] }
    skip            : set True to skip this case (endpoint not built yet)
    """
    id:              str
    method:          str
    endpoint:        str
    body:            dict | None = None
    params:          dict | None = None
    expected_status: int         = 200
    expected_body:   dict | None = None
    contains:        dict | None = None
    extract:         dict | None = None
    skip:            bool        = False


# =============================================================================
# Items API test cases
# Matches what main.py currently has:
#   GET  /           → 200
#   GET  /items      → 200  (returns LocalStage list)
#   POST /items      → 201  (after fix in main.py)
#   GET  /items/{id} → 200 if found, 404 if not (after fix in main.py)
# =============================================================================

ITEMS_TEST_CASES = [

    ApiCase(
        id            = "health check",
        method        = "get",
        endpoint      = "/",
        expected_body = {"status": "success", "message": "Hello World"},
    ),

    ApiCase(
        id       = "list all items — extract first item id and name",
        method   = "get",
        endpoint = "/items",
        contains = {"count": 5},
        extract  = {
            # Store the first item's id and name for use in later cases
            "item_id":   ["data", 0, "id"],
            "item_name": ["data", 0, "name"],
        },
    ),

    ApiCase(
        id       = "get item by extracted id",
        method   = "get",
        endpoint = "/items/{item_id}",    # {item_id} resolved from store
        contains = {"status": "success"},
    ),

    ApiCase(
        id              = "create new item",
        method          = "post",
        endpoint        = "/items",
        body            = {"name": "New Widget", "price": 9.99},
        expected_status = 201,            
        contains        = {"status": "success"},
        extract         = {
            "new_item_id": ["data", "id"],
        },
    ),

    ApiCase(
        id              = "get created item by new id",
        method          = "get",
        endpoint        = "/items/{new_item_id}",
        contains        = {"status": "success"},
    ),

    # ---- cases below need endpoints not yet in main.py ----

    ApiCase(
        id              = "update created item",
        method          = "put",
        endpoint        = "/items/{new_item_id}",
        body            = {"name": "Updated Widget", "price": 14.99},
        contains        = {"status": "success"},
        skip            = True,           # PUT /items/{id} not built yet
    ),

    ApiCase(
        id              = "delete created item",
        method          = "delete",
        endpoint        = "/items/{new_item_id}",
        expected_status = 204,
        skip            = True,           # DELETE /items/{id} not built yet
    ),

    ApiCase(
        id              = "get deleted item returns 404",
        method          = "get",
        endpoint        = "/items/{new_item_id}",
        expected_status = 404,
        skip            = True,           # depends on delete being built first
    ),

]


# =============================================================================
# Validation / edge case test cases
# =============================================================================

VALIDATION_TEST_CASES = [

    ApiCase(
        id              = "get nonexistent item returns 404",
        method          = "get",
        endpoint        = "/items/00000000-0000-0000-0000-000000000000",
        expected_status = 404,
    ),

    ApiCase(
        id              = "create item — missing name returns 422",
        method          = "post",
        endpoint        = "/items",
        body            = {"price": 9.99},   # name is required by Item model
        expected_status = 422,
    ),

    ApiCase(
        id              = "create item — missing price returns 422",
        method          = "post",
        endpoint        = "/items",
        body            = {"name": "No Price"},
        expected_status = 422,
    ),

]


# =============================================================================
# Auth flow — skip all until auth endpoints are built
# =============================================================================

AUTH_TEST_CASES = [

    ApiCase(
        id              = "login — extract token",
        method          = "post",
        endpoint        = "/auth/login",
        body            = {"email": "user@example.com", "password": "secret"},
        expected_status = 200,
        extract         = {
            "auth_token": ["data", "token"],
            "user_id":    ["data", "user", "id"],
        },
        skip = True,   # /auth/login not built yet
    ),

    ApiCase(
        id       = "get own profile",
        method   = "get",
        endpoint = "/users/{user_id}",
        contains = {"email": "user@example.com"},
        skip     = True,
    ),

    ApiCase(
        id              = "logout",
        method          = "post",
        endpoint        = "/auth/logout",
        expected_status = 200,
        skip            = True,
    ),

]