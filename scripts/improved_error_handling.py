#!/usr/bin/env python3
"""
Example of how we could improve error messages further
"""

import httpx

def get_better_error_message(e: Exception) -> str:
    """Get a more descriptive error message based on exception type"""
    error_msg = str(e)

    # If we have a non-empty message, use it
    if error_msg:
        return error_msg

    # Otherwise, provide specific messages based on exception type
    if isinstance(e, httpx.ConnectError):
        return "Failed to connect to Definite API server"
    elif isinstance(e, httpx.TimeoutException):
        return "Query timed out after 2 minutes"
    elif isinstance(e, httpx.NetworkError):
        return "Network error while communicating with Definite API"
    elif isinstance(e, httpx.ProtocolError):
        return "Protocol error in API communication"
    elif isinstance(e, ConnectionError):
        return "Connection error with Definite API"
    elif isinstance(e, TimeoutError):
        return "Request timed out"
    else:
        return "Query failed with unknown error"


# Test it
print("Testing improved error messages:")
print("=" * 50)

test_exceptions = [
    httpx.ConnectError(""),
    httpx.TimeoutException(""),
    httpx.NetworkError(""),
    httpx.ProtocolError(""),
    ConnectionError(""),
    Exception(""),
    httpx.ConnectError("Specific error: Connection refused"),
]

for exc in test_exceptions:
    print(f"\n{type(exc).__name__} with message '{str(exc)}':")
    print(f"  → {get_better_error_message(exc)}")

print("\n" + "=" * 50)
print("This would give users much clearer error messages!")