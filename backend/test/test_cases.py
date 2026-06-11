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
# Matches the current backend routes:
#   GET  /            → 200
#   GET  /products    → 200
#   POST /products    → 201
#   GET  /products/{id} → 200 if found, 404 if not
# =============================================================================

ITEMS_TEST_CASES = [
    ApiCase(
        id            = "health check",
        method        = "get",
        endpoint      = "/",
        expected_body = {"message": "Dress E-Commerce API", "version": "1.0.0"},
    ),

    ApiCase(
        id            = "list products",
        method        = "get",
        endpoint      = "/products",
        expected_status = 200,
    ),

]


# =============================================================================
# Validation / edge case test cases
# =============================================================================

VALIDATION_TEST_CASES = [
    ApiCase(
        id            = "health check",
        method        = "get",
        endpoint      = "/",
        expected_body = {"message": "Dress E-Commerce API", "version": "1.0.0"},
    ),
    ApiCase(
        id            = "chat agent",
        method        = "post",
        endpoint      = "/chat/agent",
        body          = {"message": "Hello AI, how are you?", "session_id": "test_ai_session"},
        expected_status = 200,
    ),
    ApiCase(
        id            = "get chat history",
        method        = "get",
        endpoint      = "/chat/session/test_ai_session/history",
        expected_status = 200,
    ),
]


# =============================================================================
# Auth flow — skip all until auth endpoints are built
# =============================================================================

AUTH_TEST_CASES = [

    # ApiCase(
    #     id            = "register user",
    #     method        = "post",
    #     endpoint      = "/user/register",
    #     body          = {
    #         "email": "testuser_api@example.com",
    #         "full_name": "Test User API",
    #         "username": "testuser_api",
    #         "password": "password123",
    #         "phone": "1234567890"
    #     },
    #     expected_status = 200,
    #     contains      = {"email": "testuser_api@example.com"},
    # ),
    ApiCase(
        id            = "login user",
        method        = "post",
        endpoint      = "/user/login",
        body          = {"email": "testuser_api@example.com", "password": "password123"},
        expected_status = 200,
        extract       = {"user_session_id": ["session_id"]},
    ),
    ApiCase(
        id            = "update user",
        method        = "put",
        endpoint      = "/user/update?session_id={user_session_id}",
        body          = {"full_name": "Updated Test User API"},
        expected_status = 200,
        contains      = {"full_name": "Updated Test User API"},
    ),
    ApiCase(
        id            = "get current user",
        method        = "get",
        endpoint      = "/user/me?session_id={user_session_id}",
        expected_status = 200,
        contains      = {"email": "testuser_api@example.com"},
    ),
    ApiCase(
        id            = "create address",
        method        = "post",
        endpoint      = "/addresses/",
        body          = {
            "name": "Home Address",
            "phone": "9876543210",
            "address": "123 Test St",
            "city": "Test City",
            "state": "Test State",
            "pincode": "123456",
            "session_id": "{user_session_id}"
        },
        expected_status = 200,
        extract       = {"address_id": ["id"]},
    ),
    ApiCase(
        id            = "get addresses by session",
        method        = "get",
        endpoint      = "/addresses/{user_session_id}",
        expected_status = 200,
    ),
    ApiCase(
        id            = "get address detail",
        method        = "get",
        endpoint      = "/addresses/detail/{address_id}",
        expected_status = 200,
        contains      = {"city": "Test City"},
    ),
    ApiCase(
        id            = "create product",
        method        = "post",
        endpoint      = "/products",
        body          = {
            "name": "Test Dress",
            "description": "A beautiful dress",
            "price": 25.5,
            "stock": 10,
            "image_url": "https://example.com/dress.jpg"
        },
        expected_status = 200,
        extract       = {"product_id": ["id"]},
    ),

    ApiCase(
        id            = "get product by id",
        method        = "get",
        endpoint      = "/products/{product_id}",
        contains      = {"name": "Test Dress"},
    ),

    ApiCase(
        id            = "update product",
        method        = "put",
        endpoint      = "/products/{product_id}",
        body          = {"price": 30.0},
        contains      = {"price": 30.0},
    ),

    ApiCase(
        id            = "add item to cart",
        method        = "post",
        endpoint      = "/cart/items",
        body          = {
            "product_id": "{product_id}",  # Assuming product with ID 2 exists
            "quantity": 2,
            "session_id": "{user_session_id}"
        },
        expected_status = 200,
        extract       = {"cart_item_id": ["item_id"]},
    ),
    ApiCase(
        id            = "get cart",
        method        = "get",
        endpoint      = "/cart/{user_session_id}",
        expected_status = 200,
    ),
    ApiCase(
        id            = "update cart item",
        method        = "put",
        endpoint      = "/cart/items/{cart_item_id}?session_id={user_session_id}",
        body          = {"quantity": 5},
        expected_status = 200,
        expected_body = {"message": "Cart item updated"},
    ),
    ApiCase(
        id            = "remove item from cart",
        method        = "delete",
        endpoint      = "/cart/items/{cart_item_id}?session_id={user_session_id}",
        expected_status = 200,
        expected_body = {"message": "Item removed from cart"},
    ),
    ApiCase(
        id            = "clear cart",
        method        = "delete",
        endpoint      = "/cart/{user_session_id}",
        expected_status = 200,
        expected_body = {"message": "Cart cleared"},
    ),
    # ApiCase(
    #     id            = "create order",
    #     method        = "post",
    #     endpoint      = "/orders/",
    #     body          = {
    #         "session_id": "{user_session_id}",
    #         "address_id": "{address_id}"
    #     },
    #     expected_status = 200,
    #     extract       = {"order_id": ["id"]},
    # ),
    ApiCase(
        id            = "get orders by session",
        method        = "get",
        endpoint      = "/orders/{user_session_id}",
        expected_status = 200,
    ),
    # ApiCase(
    #     id            = "get order detail",
    #     method        = "get",
    #     endpoint      = "/orders/detail/{order_id}",
    #     expected_status = 200,
    # ),
    # ApiCase(
    #     id            = "update order status",
    #     method        = "put",
    #     endpoint      = "/orders/{order_id}/status?status=Confirmed",
    #     expected_status = 200,
    # ),
    ApiCase(
        id            = "create review",
        method        = "post",
        endpoint      = "/reviews/",
        body          = {
            "rating": 5,
            "comment": "Great product!",
            "product_id": "{product_id}",
            "session_id": "{user_session_id}"
        },
        expected_status = 200,
        extract       = {"review_id": ["id"]},
    ),
    ApiCase(
        id            = "get product reviews",
        method        = "get",
        endpoint      = "/reviews/product/{product_id}",
        expected_status = 200,
    ),
    ApiCase(
        id            = "get my review",
        method        = "get",
        endpoint      = "/reviews/my-review/{product_id}?session_id={user_session_id}",
        expected_status = 200,
        contains      = {"rating": 5},
    ),
    ApiCase(
        id            = "update review",
        method        = "put",
        endpoint      = "/reviews/{review_id}?session_id={user_session_id}",
        body          = {"rating": 4, "comment": "Good product"},
        expected_status = 200,
        contains      = {"rating": 4},
    ),
    ApiCase(
        id            = "delete review",
        method        = "delete",
        endpoint      = "/reviews/{review_id}?session_id={user_session_id}",
        expected_status = 200,
        expected_body = {"message": "Review deleted successfully"},
    ),

    ApiCase(
        id            = "delete product",
        method        = "delete",
        endpoint      = "/products/{product_id}",
        expected_body = {"message": "Product deleted successfully"},
    ),

    ApiCase(
        id            = "product deleted returns 404",
        method        = "get",
        endpoint      = "/products/{product_id}",
        expected_status = 404,
        expected_body = {"detail": "Product not found"},
    ),

]


# =============================================================================
# Cart API test cases
# =============================================================================

CART_TEST_CASES = [
   
]

# =============================================================================
# Order API test cases
# =============================================================================

ORDER_TEST_CASES = [
    
]

# =============================================================================
# Review API test cases
# =============================================================================

REVIEW_TEST_CASES = [
    
]
# =============================================================================
# AI Chat API test cases
# =============================================================================

CHAT_TEST_CASES = [
    ApiCase(
        id            = "chat agent",
        method        = "post",
        endpoint      = "/chat/agent",
        body          = {"message": "Hello AI, how are you?", "session_id": "test_ai_session"},
        expected_status = 200,
    ),
    ApiCase(
        id            = "get chat history",
        method        = "get",
        endpoint      = "/chat/session/test_ai_session/history",
        expected_status = 200,
    ),
]