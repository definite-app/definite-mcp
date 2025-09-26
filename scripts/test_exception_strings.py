#!/usr/bin/env python3
"""
Test which exceptions produce empty strings
"""

import sys

print("Testing exceptions that might produce empty strings...")
print("=" * 60)

# Test various exception types
exceptions_to_test = [
    (Exception(""), "Exception with empty string"),
    (Exception(), "Exception with no args"),
    (ValueError(""), "ValueError with empty string"),
    (RuntimeError(""), "RuntimeError with empty string"),
    (OSError(""), "OSError with empty string"),
    (KeyError(""), "KeyError with empty string"),
    (TypeError(""), "TypeError with empty string"),
    (ConnectionError(""), "ConnectionError with empty string"),
]

for exc, description in exceptions_to_test:
    print(f"\n{description}:")
    print(f"  Type: {type(exc).__name__}")
    print(f"  str(e): '{str(exc)}'")
    print(f"  Is empty: {str(exc) == ''}")
    print(f"  repr(e): {repr(exc)}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("Many Python exceptions can have empty string representations!")
print("This is why 'Query failed with unknown error' can occur.")

# Test httpx specific exceptions
print("\n" + "=" * 60)
print("Testing httpx-specific scenarios...")

try:
    import httpx

    # Test httpx exceptions
    httpx_exceptions = [
        httpx.TimeoutException(""),
        httpx.ConnectError(""),
        httpx.ReadError(""),
        httpx.WriteError(""),
        httpx.ProtocolError(""),
    ]

    for exc in httpx_exceptions:
        print(f"\n{type(exc).__name__}:")
        print(f"  str(e): '{str(exc)}'")
        print(f"  Is empty: {str(exc) == ''}")

except ImportError:
    print("httpx not available in this context")