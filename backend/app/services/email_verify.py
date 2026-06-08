"""Optional email verification via Reacher / ZeroBounce / Hunter.

Returns a status string: "valid", "invalid", "risky", or "unknown".
Gracefully returns "unknown" when no provider is configured.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


def _is_set(value: str | None) -> bool:
    return bool(value) and not str(value).startswith("replace_")


def verify_email(
    email: str,
    *,
    reacher_url: str | None = None,
    reacher_key: str | None = None,
    zerobounce_key: str | None = None,
    hunter_key: str | None = None,
) -> str:
    if not email:
        return "unknown"

    # Prefer self-hosted Reacher if configured.
    if _is_set(reacher_url):
        try:
            headers = {"Content-Type": "application/json"}
            if _is_set(reacher_key):
                headers["Authorization"] = reacher_key
            resp = httpx.post(
                f"{reacher_url.rstrip('/')}/v0/check_email",
                headers=headers,
                json={"to_email": email},
                timeout=30.0,
            )
            resp.raise_for_status()
            reachable = resp.json().get("is_reachable", "unknown")
            return {"safe": "valid", "invalid": "invalid", "risky": "risky"}.get(reachable, "unknown")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Reacher verification failed: %s", exc)

    if _is_set(zerobounce_key):
        try:
            resp = httpx.get(
                "https://api.zerobounce.net/v2/validate",
                params={"api_key": zerobounce_key, "email": email},
                timeout=30.0,
            )
            resp.raise_for_status()
            status = resp.json().get("status", "unknown")
            return {"valid": "valid", "invalid": "invalid", "catch-all": "risky"}.get(status, "unknown")
        except Exception as exc:  # noqa: BLE001
            logger.warning("ZeroBounce verification failed: %s", exc)

    return "unknown"
