import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
import aiofiles

# Base folder for context files
CONTEXT_STORE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "context_store")
)

class PropertyOwnerLink(SQLModel, table=True):
    __tablename__ = "property_owner_links"
    owner_id: str = Field(foreign_key="owners.id", primary_key=True)
    property_id: str = Field(foreign_key="properties.id", primary_key=True)


class Owner(SQLModel, table=True):
    __tablename__ = "owners"
    id: str = Field(default=None, primary_key=True)
    name: str
    phone: str = Field(index=True, unique=True)
    email: str
    
    properties: List["Property"] = Relationship(back_populates="owners", link_model=PropertyOwnerLink)


class Property(SQLModel, table=True):
    __tablename__ = "properties"
    id: str = Field(default=None, primary_key=True)
    name: str = Field(index=True) # e.g. "Musterstraße 12"
    address: str
    zipcode: str
    
    owners: List[Owner] = Relationship(back_populates="properties", link_model=PropertyOwnerLink)
    flats: List["Flat"] = Relationship(back_populates="property")


class Flat(SQLModel, table=True):
    __tablename__ = "flats"
    id: str = Field(default=None, primary_key=True)
    flat_no: str = Field(index=True) # e.g. "Apt 3B"
    property_id: str = Field(foreign_key="properties.id")
    tenant_id: Optional[str] = Field(default=None, foreign_key="tenants.id")
    is_rented: bool = Field(default=False)
    
    property: Property = Relationship(back_populates="flats")
    tenant: Optional["Tenant"] = Relationship(back_populates="flat")


class Tenant(SQLModel, table=True):
    __tablename__ = "tenants"
    id: str = Field(default=None, primary_key=True)
    name: str
    phone: str = Field(index=True, unique=True)
    email: str
    
    flat: Optional[Flat] = Relationship(back_populates="tenant")


class Vendor(SQLModel, table=True):
    __tablename__ = "vendors"
    id: str = Field(default=None, primary_key=True)
    name: str
    phone: str = Field(index=True, unique=True)
    email: str
    category: str = Field(index=True) # e.g. "plumbing", "hvac", "locksmith", "electrical"
    zipcode_coverage: str # Comma-separated list of zip codes covered


class Ticket(SQLModel, table=True):
    __tablename__ = "tickets"
    id: str = Field(default=None, primary_key=True)
    property_id: str = Field(foreign_key="properties.id")
    flat_no: str
    tenant_id: Optional[str] = Field(default=None, foreign_key="tenants.id")
    vendor_id: Optional[str] = Field(default=None, foreign_key="vendors.id")
    status: str = Field(default="NEW") # NEW, PENDING_APPROVAL, APPROVED, DISPATCHED, RESOLVED, CLOSED
    priority: str = Field(default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    issue_category: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalRequest(SQLModel, table=True):
    __tablename__ = "approval_requests"
    id: str = Field(default=None, primary_key=True)
    call_id: str = Field(index=True)
    ticket_id: str = Field(foreign_key="tickets.id")
    details: str
    status: str = Field(default="PENDING") # PENDING, APPROVED, REJECTED, TIMEOUT
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Helper functions for filesystem property-centric context logs

def get_ticket_dir(property_name: str, flat_no: str, ticket_id: str) -> str:
    # Clean up strings for folder naming
    safe_prop = property_name.replace(" ", "_").replace("/", "-").lower()
    safe_flat = flat_no.replace(" ", "_").replace("/", "-").lower()
    return os.path.join(
        CONTEXT_STORE_DIR,
        "properties",
        safe_prop,
        "flats",
        safe_flat,
        "tickets",
        f"ticket_{ticket_id}",
    )


async def init_flat_details(property_name: str, flat_no: str, owners_data: List[dict], tenant_data: dict):
    """Initializes flat_details.json and property_details.json in the context store."""
    safe_prop = property_name.replace(" ", "_").replace("/", "-").lower()
    safe_flat = flat_no.replace(" ", "_").replace("/", "-").lower()
    
    prop_dir = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop)
    flat_dir = os.path.join(prop_dir, "flats", safe_flat)
    
    os.makedirs(flat_dir, exist_ok=True)
    
    prop_details_path = os.path.join(prop_dir, "property_details.json")
    if not os.path.exists(prop_details_path):
        async with aiofiles.open(prop_details_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps({
                "property_name": property_name,
                "owners": owners_data,
                "created_at": datetime.utcnow().isoformat()
            }, indent=2))
            
    flat_details_path = os.path.join(flat_dir, "flat_details.json")
    async with aiofiles.open(flat_details_path, "w", encoding="utf-8") as f:
        await f.write(json.dumps({
            "flat_no": flat_no,
            "tenant": tenant_data,
            "updated_at": datetime.utcnow().isoformat()
        }, indent=2))



async def read_master_context(property_name: str, flat_no: str, ticket_id: str) -> Optional[Dict[str, Any]]:
    ticket_dir = get_ticket_dir(property_name, flat_no, ticket_id)
    filepath = os.path.join(ticket_dir, "master_context.json")
    if not os.path.exists(filepath):
        return None
    async with aiofiles.open(filepath, "r", encoding="utf-8") as f:
        content = await f.read()
        return json.loads(content)


async def write_master_context(property_name: str, flat_no: str, ticket_id: str, context_data: Dict[str, Any]):
    ticket_dir = get_ticket_dir(property_name, flat_no, ticket_id)
    os.makedirs(ticket_dir, exist_ok=True)
    filepath = os.path.join(ticket_dir, "master_context.json")
    async with aiofiles.open(filepath, "w", encoding="utf-8") as f:
        await f.write(json.dumps(context_data, indent=2))


async def append_timeline_event(
    property_name: str,
    flat_no: str,
    ticket_id: str,
    event_type: str,
    author: str,
    description: str,
    payload: Optional[Dict[str, Any]] = None
):
    """Appends an event to the ticket's master_context timeline."""
    context = await read_master_context(property_name, flat_no, ticket_id)
    if not context:
        # Create baseline context if missing
        context = {
            "ticket_id": ticket_id,
            "property_name": property_name,
            "flat_no": flat_no,
            "timeline": []
        }
        
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "type": event_type,
        "author": author,
        "description": description,
        "payload": payload or {}
    }
    context["timeline"].append(event)
    
    # Update quick metadata fields if provided in payload
    if payload:
        for key in ["status", "priority", "issue_category", "description", "assigned_vendor", "next_steps", "suggestions"]:
            if key in payload:
                context[key] = payload[key]
                
    await write_master_context(property_name, flat_no, ticket_id, context)
    return context
