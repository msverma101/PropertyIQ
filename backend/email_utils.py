import os
from typing import Optional, List, Dict, Any
import httpx


async def send_email(
    to_email: str,
    subject: str,
    body: str,
    cc_emails: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Send a plain-text email via Resend. Returns {status, provider_id, error}."""
    api_key = os.environ.get("RESEND_API_KEY")
    from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")

    if not api_key:
        return {"status": "failed", "provider_id": None, "error": "RESEND_API_KEY not set"}

    payload: Dict[str, Any] = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body,
    }
    if cc_emails:
        payload["cc"] = cc_emails

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code in (200, 202):
            return {
                "status": "sent",
                "provider_id": response.json().get("id"),
                "error": None,
            }
        return {
            "status": "failed",
            "provider_id": None,
            "error": f"Resend HTTP {response.status_code}: {response.text}",
        }
    except Exception as e:
        return {"status": "failed", "provider_id": None, "error": str(e)}
