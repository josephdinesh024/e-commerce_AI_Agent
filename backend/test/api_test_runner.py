import re
import pytest
import requests as req_lib
from typing import Any


# =============================================================================
# ApiTestRunner — the core engine
# =============================================================================

class ApiTestRunner:
    """
    Wraps either a FastAPI TestClient or a requests.Session.
    Provides:
      - request()       make HTTP calls (GET/POST/PUT/PATCH/DELETE)
      - extract()       pull values from response JSON by path
      - resolve()       inject stored values into endpoints / body
      - assert_response() validate status + body

    Usage — FastAPI TestClient:
        from fastapi.testclient import TestClient
        from myapp.main import app
        runner = ApiTestRunner(client=TestClient(app))

    Usage — real HTTP (any API):
        runner = ApiTestRunner(base_url="https://api.example.com")
        runner = ApiTestRunner(base_url="http://localhost:8000")
    """

    def __init__(self, client=None, base_url: str = None, headers: dict = None):
        """
        Provide EITHER client (TestClient) OR base_url (str), not both.

        client   : FastAPI TestClient instance
        base_url : root URL for requests-based calls, e.g. "http://localhost:8000"
        headers  : default headers added to every request (auth tokens, content-type, etc.)
        """
        if client is None and base_url is None:
            raise ValueError("Provide either client= or base_url=")
        if client is not None and base_url is not None:
            raise ValueError("Provide only one of client= or base_url=, not both")

        self._client   = client        # FastAPI TestClient or None
        self._base_url = base_url      # str or None
        self._session  = req_lib.Session() if base_url else None
        self._headers  = headers or {}

        # Shared state store — values extracted from responses are saved here
        # by name and reused in later requests.
        # e.g.  store["item_id"] = "abc123"
        self.store: dict[str, Any] = {}

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _make_request(self, method: str, endpoint: str, **kwargs):
        """
        Route the call to either TestClient or requests.Session.
        kwargs are passed through directly (json=, params=, data=, headers=).
        """
        method = method.lower()

        # Merge default headers with per-request headers
        merged_headers = {**self._headers, **kwargs.pop("headers", {})}
        if merged_headers:
            kwargs["headers"] = merged_headers

        if self._client:
            # --- FastAPI TestClient path ---
            fn = getattr(self._client, method, None)
            if fn is None:
                raise ValueError(f"Unsupported HTTP method: {method}")
            return fn(endpoint, **kwargs)

        else:
            # --- requests.Session path ---
            url = self._base_url.rstrip("/") + endpoint
            fn = getattr(self._session, method, None)
            if fn is None:
                raise ValueError(f"Unsupported HTTP method: {method}")
            return fn(url, **kwargs)

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def request(
        self,
        method:   str,
        endpoint: str,
        body:     dict | None = None,
        params:   dict | None = None,
        headers:  dict | None = None,
    ):
        """
        Make an HTTP request.

        method   : "get" | "post" | "put" | "patch" | "delete"
        endpoint : path like "/items/{id}" — placeholders resolved before call
        body     : JSON request body (POST/PUT/PATCH)
        params   : URL query parameters  e.g. {"page": 1, "limit": 10}
        headers  : per-request headers (merged with default headers)

        Placeholders in endpoint AND body values are resolved from self.store
        before the request is sent.

        Returns the response object (same shape for both TestClient/requests).
        """
        endpoint = self.resolve_placeholders(endpoint)

        kwargs: dict = {}
        if body    : kwargs["json"]    = self.resolve_body(body)
        if params  : kwargs["params"]  = self.resolve_body(params)
        if headers : kwargs["headers"] = headers

        return self._make_request(method, endpoint, **kwargs)

    def extract(self, response, path: list) -> Any:
        """
        Extract a value from a response JSON by following a key path.

        path is a list of keys/indices to traverse:
            ["data", 0, "id"]   →  response.json()["data"][0]["id"]
            ["token"]           →  response.json()["token"]

        Raises a clear error if the path doesn't exist.
        """
        data = response.json()
        for step in path:
            try:
                data = data[step]
            except (KeyError, IndexError, TypeError) as e:
                raise KeyError(
                    f"Extract failed at step '{step}' in path {path}. "
                    f"Data at this point: {data!r}"
                ) from e
        return data

    def extract_many(self, response, extract_map: dict[str, list]) -> dict:
        """
        Extract multiple values in one call and save them all into self.store.

        extract_map: { store_key: path, ... }
        Example:
            extract_map = {
                "item_id":   ["data", 0, "id"],
                "item_name": ["data", 0, "name"],
            }
        After this call:
            self.store["item_id"]   == "abc123"
            self.store["item_name"] == "Widget"
        """
        for store_key, path in extract_map.items():
            value = self.extract(response, path)
            self.store[store_key] = value
        return self.store

    def resolve_placeholders(self, endpoint: str) -> str:
        """
        Replace {placeholder} tokens in an endpoint string with values
        from self.store.

        "/items/{item_id}/reviews/{review_id}"
        + store = {"item_id": "42", "review_id": "7"}
        → "/items/42/reviews/7"

        Raises KeyError with a clear message if a placeholder isn't in store.
        """
        pattern = re.compile(r"\{(\w+)\}")
        matches = pattern.findall(endpoint)

        for key in matches:
            if key not in self.store:
                raise KeyError(
                    f"Endpoint placeholder '{{{key}}}' not found in store. "
                    f"Current store keys: {list(self.store.keys())}"
                )
            endpoint = endpoint.replace(f"{{{key}}}", str(self.store[key]))

        return endpoint

    def resolve_body(self, body: dict) -> dict:
        """
        Replace string values in a body/params dict that look like {placeholder}
        with values from self.store.

        body = {"user_id": "{current_user_id}", "role": "admin"}
        + store = {"current_user_id": "99"}
        → {"user_id": "99", "role": "admin"}

        Only top-level string values are resolved (not nested dicts).
        For nested bodies, resolve explicitly before passing.
        """
        resolved = {}
        for k, v in body.items():
            if isinstance(v, str):
                inner = re.fullmatch(r"\{(\w+)\}", v)
                if inner and inner.group(1) in self.store:
                    resolved[k] = self.store[inner.group(1)]
                else:
                    resolved[k] = v
            else:
                resolved[k] = v
        return resolved

    def assert_response(
        self,
        response,
        expected_status: int          = 200,
        expected_body:   dict | None  = None,
        contains:        dict | None  = None,
    ):
        """
        Assert on a response.

        expected_status : exact HTTP status code check (default 200)
        expected_body   : full exact match of response.json()
        contains        : partial match — check only these keys exist with these values
                          useful when the response has many fields and you only care about some

        Example:
            runner.assert_response(res, expected_status=201,
                contains={"name": "Alice", "is_admin": False})
        """
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Body: {response.text}"
        )

        if expected_body is not None:
            assert response.json() == expected_body, (
                f"Body mismatch.\nExpected: {expected_body}\nGot: {response.json()}"
            )

        if contains is not None:
            body = response.json()
            for key, value in contains.items():
                assert key in body, f"Key '{key}' not found in response: {body}"
                assert body[key] == value, (
                    f"Key '{key}': expected {value!r}, got {body[key]!r}"
                )

    def set(self, key: str, value: Any):
        """Manually store a value — useful for hardcoded seeds or test setup."""
        self.store[key] = value

    def get(self, key: str) -> Any:
        """Retrieve a stored value by name."""
        if key not in self.store:
            raise KeyError(f"'{key}' not found in store. Available: {list(self.store.keys())}")
        return self.store[key]

    def clear(self):
        """Clear all stored values — call between independent test suites."""
        self.store.clear()