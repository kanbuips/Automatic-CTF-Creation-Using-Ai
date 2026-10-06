"""Auth (API key). An empty configured key disables auth."""
import hmac


def verify_api_key(provided: str | None, expected: str) -> bool:
    if not expected:
        return True
    return provided is not None and hmac.compare_digest(provided.encode(), expected.encode())
