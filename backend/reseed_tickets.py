"""
One-off script to wipe all existing tickets and reseed a clean, varied set.

Usage:
    cd backend && uv run python reseed_tickets.py

Only touches the `tickets` and `approval_requests` tables. Tenants, properties,
vendors, owners, flats, and on-disk context store files are left intact.
"""
import asyncio
from datetime import datetime, timedelta

from sqlalchemy import text

from shared import async_session_maker
from models import Ticket


NOW = datetime.utcnow()


def _ago(hours: float) -> datetime:
    return NOW - timedelta(hours=hours)


SEED_TICKETS = [
    Ticket(
        id="ticket_seed_001",
        property_id="prop_001",
        flat_no="Apt 3B",
        tenant_id="tenant_001",
        vendor_id="vendor_001",
        status="DISPATCHED",
        priority="CRITICAL",
        issue_category="hvac",
        description=(
            "Heating completely stopped overnight, radiators cold, 4-year-old in flat, "
            "ambient 12°C."
        ),
        created_at=_ago(4),
        updated_at=_ago(0.5),
    ),
    Ticket(
        id="ticket_seed_002",
        property_id="prop_001",
        flat_no="Apt 2A",
        tenant_id="tenant_002",
        vendor_id="vendor_002",
        status="APPROVED",
        priority="MEDIUM",
        issue_category="hvac",
        description=(
            "Boiler making loud knocking sound at night, otherwise still heats. "
            "Wants it checked."
        ),
        created_at=_ago(14),
        updated_at=_ago(8),
    ),
    Ticket(
        id="ticket_seed_003",
        property_id="prop_002",
        flat_no="Apt 1",
        tenant_id="tenant_003",
        vendor_id=None,
        status="NEW",
        priority="MEDIUM",
        issue_category="electrical",
        description=(
            "Kitchen circuit trips every time the kettle and microwave run together."
        ),
        created_at=_ago(2),
        updated_at=_ago(2),
    ),
    Ticket(
        id="ticket_seed_004",
        property_id="prop_002",
        flat_no="Apt 2",
        tenant_id="tenant_004",
        vendor_id="vendor_003",
        status="PENDING_APPROVAL",
        priority="HIGH",
        issue_category="plumbing",
        description=(
            "Bathroom drain backing up, slow for two days, water now reaching the floor."
        ),
        created_at=_ago(6),
        updated_at=_ago(1),
    ),
    Ticket(
        id="ticket_seed_005",
        property_id="prop_003",
        flat_no="Apt 4",
        tenant_id="tenant_005",
        vendor_id="vendor_004",
        status="RESOLVED",
        priority="CRITICAL",
        issue_category="locksmith",
        description=(
            "Lock jammed — key won't turn, tenant locked out at 11pm."
        ),
        created_at=_ago(38),
        updated_at=_ago(36),
    ),
    Ticket(
        id="ticket_seed_006",
        property_id="prop_001",
        flat_no="Apt 3B",
        tenant_id="tenant_001",
        vendor_id="vendor_005",
        status="CLOSED",
        priority="LOW",
        issue_category="electrical",
        description=(
            "Hallway light flickered for weeks then died. Electrician swapped fixture."
        ),
        created_at=_ago(70),
        updated_at=_ago(60),
    ),
]


async def reseed() -> None:
    async with async_session_maker() as session:
        # Wipe approval_requests first (FK references tickets.id), then tickets.
        await session.execute(text("DELETE FROM approval_requests"))
        await session.execute(text("DELETE FROM tickets"))
        await session.commit()
        print("Wiped tickets and approval_requests.")

        for t in SEED_TICKETS:
            session.add(t)
        await session.commit()
        print(f"Inserted {len(SEED_TICKETS)} varied tickets.")


if __name__ == "__main__":
    asyncio.run(reseed())
