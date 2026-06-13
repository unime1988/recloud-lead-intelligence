"""CRM / webhook export placeholders.

These are intentionally lightweight wrappers. Real CRM sync is disabled by
default (ENABLE_CRM_SYNC=false). No outreach is auto-sent.
"""

import logging

import httpx

logger = logging.getLogger(__name__)


def push_webhook(url: str | None, payload: dict) -> bool:
    """POST a lead payload to an n8n/webhook URL. Returns success bool."""
    if not url or str(url).startswith("replace_with"):
        logger.info("No webhook URL configured; skipping export")
        return False
    try:
        resp = httpx.post(url, json=payload, timeout=30.0)
        resp.raise_for_status()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Webhook export failed: %s", exc)
        return False


def sync_to_hubspot(api_key: str | None, lead: dict) -> bool:
    """Placeholder for HubSpot contact/company sync."""
    if not api_key or str(api_key).startswith("replace_with"):
        logger.info("HubSpot not configured; skipping CRM sync")
        return False
    logger.info("HubSpot sync placeholder invoked for %s", lead.get("company_name"))
    return False


def sync_to_baserow(api_url: str | None, api_key: str | None, lead: dict) -> bool:
    """Placeholder for Baserow row creation."""
    if not api_url or str(api_url).startswith("replace_with"):
        return False
    logger.info("Baserow sync placeholder invoked for %s", lead.get("company_name"))
    return False


def sync_to_twenty(api_url: str | None, api_key: str | None, lead: dict) -> bool:
    """Placeholder for Twenty CRM sync."""
    if not api_url or str(api_url).startswith("replace_with"):
        return False
    logger.info("Twenty CRM sync placeholder invoked for %s", lead.get("company_name"))
    return False
