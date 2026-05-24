import os
import json
import asyncio
import aiofiles
import httpx
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

from models import (
    Owner,
    Property,
    Flat,
    Tenant,
    Vendor,
    Ticket,
    ApprovalRequest,
    PropertyOwnerLink,
    CONTEXT_STORE_DIR,
    read_master_context,
    append_timeline_event,
)
from shared import (
    async_engine,
    async_session_maker,
    active_call_sessions,
    manager,
)
from mcp_tools import mcp
from email_utils import send_email

# FastAPI Lifespan and Instance
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Perform startup validation
    if not os.path.exists(CONTEXT_STORE_DIR):
        os.makedirs(CONTEXT_STORE_DIR, exist_ok=True)
    yield
    # Cleanup async engine on shutdown
    await async_engine.dispose()

app = FastAPI(title="HelloTheo TenantOps API", lifespan=lifespan)

# Allow CORS for Next.js dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount FastMCP HTTP ASGI app under /mcp using SSE transport
mcp_app = mcp.http_app(transport="sse")
app.mount("/mcp", mcp_app)


# --- API Endpoints ---

@app.get("/api/caller-lookup")
async def caller_lookup(phone: Optional[str] = None, call_id: Optional[str] = None):
    """
    Pre-call webhook fired by ElevenLabs at the start of every conversation.
    For PSTN inbound calls, `phone` is the caller-id and we resolve the tenant/owner/vendor.
    For browser/web inbound calls, `phone` is empty — we fall through to the unknown-caller
    branch, where the agent verbally asks the caller for their name and calls `lookup_tenant`.
    """
    # Clean phone number (remove spaces and ensure '+' prefix). Empty allowed for browser calls.
    phone = (phone or "").strip()
    if phone and not phone.startswith("+"):
        phone = "+" + phone
    
    # Generate fallback call_id if not supplied
    resolved_call_id = call_id or f"call_{int(datetime.utcnow().timestamp())}"
    
    # If no phone (browser/web call), skip DB lookups and go straight to the unknown branch.
    if not phone:
        active_call_sessions[resolved_call_id] = {
            "caller_name": "Guest",
            "caller_type": "unknown",
            "phone": "",
        }
        await manager.broadcast(resolved_call_id, {
            "event": "call_start",
            "call_id": resolved_call_id,
            "caller_name": "Guest",
            "caller_type": "unknown",
            "property_name": None,
            "flat_no": None,
        })
        return {
            "caller_found": False,
            "caller_name": "Guest",
            "caller_type": "unknown",
            "call_id": resolved_call_id,
            "dynamic_variables": {
                "caller_name": "Guest",
                "caller_type": "unknown",
                "call_id": resolved_call_id,
            },
            "conversation_config_override": {
                "agent": {
                    "first_message": (
                        "Hello, thank you for calling HelloTheo property management. "
                        "May I have your full name please?"
                    ),
                    "prompt": {
                        "prompt": (
                            "You are HelloTheo's maintenance assistant. "
                            "FIRST STEP: ask the caller for their full name. "
                            "AS SOON AS they tell you their name, call the 'lookup_tenant' tool "
                            "with arguments name=<their full name> and call_id=<the active call_id>. "
                            "When lookup_tenant returns, read the 'agent_hint' field and follow it: "
                            "confirm the address back to the caller ('I see you at <address_line>, is that correct?'). "
                            "If they confirm, ask them to describe the maintenance issue in one or two sentences. "
                            "Then call 'update_master_context' once with the call_id, description, "
                            "an issue_category from {plumbing, hvac, electrical, locksmith, general}, "
                            "and a priority from {LOW, MEDIUM, HIGH, CRITICAL}. "
                            "If lookup_tenant returns status='no_match', politely ask the caller to spell "
                            "their full name and try again. Keep the call under 90 seconds."
                        )
                    },
                }
            },
        }

    async with async_session_maker() as session:
        # Check if tenant is calling
        tenant_stmt = select(Tenant).where(Tenant.phone == phone)
        tenant_result = await session.execute(tenant_stmt)
        tenant = tenant_result.scalars().first()
        
        if tenant:
            # Get tenant flat and property
            flat_stmt = select(Flat).where(Flat.tenant_id == tenant.id)
            flat_result = await session.execute(flat_stmt)
            flat = flat_result.scalars().first()
            
            if flat:
                prop_stmt = select(Property).where(Property.id == flat.property_id)
                prop_result = await session.execute(prop_stmt)
                prop = prop_result.scalars().first()
                
                if prop:
                    # Retrieve all owners for the property
                    owner_link_stmt = select(Owner).join(PropertyOwnerLink).where(PropertyOwnerLink.property_id == prop.id)
                    owner_link_result = await session.execute(owner_link_stmt)
                    prop_owners = owner_link_result.scalars().all()
                    owners_list = [{"id": o.id, "name": o.name, "email": o.email, "phone": o.phone} for o in prop_owners]

                    active_call_sessions[resolved_call_id] = {
                        "caller_name": tenant.name,
                        "caller_type": "tenant",
                        "phone": phone,
                        "property_name": prop.name,
                        "flat_no": flat.flat_no,
                        "tenant_id": tenant.id,
                        "owners": owners_list
                    }
                    
                    await manager.broadcast(resolved_call_id, {
                        "event": "call_start",
                        "call_id": resolved_call_id,
                        "caller_name": tenant.name,
                        "caller_type": "tenant",
                        "property_name": prop.name,
                        "flat_no": flat.flat_no
                    })
                    
                    return {
                        "caller_found": True,
                        "caller_name": tenant.name,
                        "caller_type": "tenant",
                        "property_name": prop.name,
                        "flat_no": flat.flat_no,
                        "call_id": resolved_call_id,
                        "dynamic_variables": {
                            "caller_name": tenant.name,
                            "caller_type": "tenant",
                            "property_name": prop.name,
                            "flat_no": flat.flat_no,
                            "call_id": resolved_call_id
                        },
                        "conversation_config_override": {
                            "agent": {
                                "first_message": f"Hello {tenant.name}, thank you for calling HelloTheo property management. I see you are calling from {prop.name}, unit {flat.flat_no}. How can I assist you with your maintenance today?",
                                "prompt": {
                                    "prompt": "You are HelloTheo's Operations Assistant. You are talking to a tenant. COMPULSORY FIRST STEP: At the very start of the call, before taking any action or calling other tools, you MUST call the 'read_context' tool with the active call_id to retrieve the property, unit, tenant, owner, and ticket details. Only after calling 'read_context' are you permitted to call update_master_context, request_manager_approval, or other tools."
                                }
                            }
                        }
                    }

        # Check if owner is calling
        owner_stmt = select(Owner).where(Owner.phone == phone)
        owner_result = await session.execute(owner_stmt)
        owner = owner_result.scalars().first()
        if owner:
            active_call_sessions[resolved_call_id] = {
                "caller_name": owner.name,
                "caller_type": "owner",
                "phone": phone,
                "owner_id": owner.id,
                "property_name": "Multiple Properties"
            }
            await manager.broadcast(resolved_call_id, {
                "event": "call_start",
                "call_id": resolved_call_id,
                "caller_name": owner.name,
                "caller_type": "owner",
                "property_name": "Multiple Properties",
                "flat_no": None
            })
            return {
                "caller_found": True,
                "caller_name": owner.name,
                "caller_type": "owner",
                "call_id": resolved_call_id,
                "dynamic_variables": {
                    "caller_name": owner.name,
                    "caller_type": "owner",
                    "call_id": resolved_call_id
                },
                "conversation_config_override": {
                    "agent": {
                        "first_message": f"Hello Mr. {owner.name}, thank you for calling HelloTheo. I recognize you as an owner on our platform. How can I help you today?",
                        "prompt": {
                            "prompt": "You are HelloTheo's Operations Assistant. You are talking to an owner. COMPULSORY FIRST STEP: At the very start of the call, before taking any action or calling other tools, you MUST call the 'read_context' tool with the active call_id to retrieve the property, unit, tenant, owner, and ticket details. Only after calling 'read_context' are you permitted to call update_master_context, request_manager_approval, or other tools."
                        }
                    }
                }
            }

        # Check if vendor is calling
        vendor_stmt = select(Vendor).where(Vendor.phone == phone)
        vendor_result = await session.execute(vendor_stmt)
        vendor = vendor_result.scalars().first()
        if vendor:
            active_call_sessions[resolved_call_id] = {
                "caller_name": vendor.name,
                "caller_type": "vendor",
                "phone": phone,
                "vendor_id": vendor.id,
                "vendor_category": vendor.category
            }
            await manager.broadcast(resolved_call_id, {
                "event": "call_start",
                "call_id": resolved_call_id,
                "caller_name": vendor.name,
                "caller_type": "vendor",
                "property_name": None,
                "flat_no": None
            })
            return {
                "caller_found": True,
                "caller_name": vendor.name,
                "caller_type": "vendor",
                "call_id": resolved_call_id,
                "dynamic_variables": {
                    "caller_name": vendor.name,
                    "caller_type": "vendor",
                    "call_id": resolved_call_id
                },
                "conversation_config_override": {
                    "agent": {
                        "first_message": f"Hello, thank you for calling HelloTheo. Is this {vendor.name}? I see you are registered as our {vendor.category} vendor. Are you calling regarding an active repair?",
                        "prompt": {
                            "prompt": "You are HelloTheo's Operations Assistant. You are talking to a vendor. COMPULSORY FIRST STEP: At the very start of the call, before taking any action or calling other tools, you MUST call the 'read_context' tool with the active call_id to retrieve the property, unit, tenant, owner, and ticket details. Only after calling 'read_context' are you permitted to call update_master_context, request_manager_approval, or other tools."
                        }
                    }
                }
            }

        # Unknown caller
        active_call_sessions[resolved_call_id] = {
            "caller_name": "Unknown",
            "caller_type": "unknown",
            "phone": phone
        }
        await manager.broadcast(resolved_call_id, {
            "event": "call_start",
            "call_id": resolved_call_id,
            "caller_name": "Guest",
            "caller_type": "unknown",
            "property_name": None,
            "flat_no": None
        })
        return {
            "caller_found": False,
            "caller_name": "Guest",
            "caller_type": "unknown",
            "call_id": resolved_call_id,
            "dynamic_variables": {
                "caller_name": "Guest",
                "caller_type": "unknown",
                "call_id": resolved_call_id
            },
            "conversation_config_override": {
                "agent": {
                    "first_message": "Hello, thank you for calling HelloTheo property management. To help me direct your call, are you calling as a tenant, owner, or vendor?",
                    "prompt": {
                        "prompt": "You are HelloTheo's Operations Assistant. You are talking to an unknown caller. Ask if they are a tenant, owner, or vendor. Once they specify, obtain their property name and unit. COMPULSORY FIRST STEP: Once property/unit details are gathered (or immediately if available), you MUST call the 'read_context' tool with the active call_id to retrieve the property, unit, tenant, owner, and ticket details. Only after calling 'read_context' are you permitted to call update_master_context, request_manager_approval, or other tools."
                    }
                }
            }
        }


@app.post("/api/calls/{call_id}/ended")
async def call_ended(call_id: str, payload: dict):
    """
    Webhook called by ElevenLabs when the call finishes.
    Receives final transcript and call summary, offloading it into the context store.

    Branches on session_info["call_type"]:
      - "vendor_dispatch": outbound vendor call ended; capture availability + email tenant.
      - otherwise:        inbound tenant call ended; save transcript on the ticket.
    """
    # 1. Retrieve session info (peek first so we can branch, then pop at the end)
    session_info = active_call_sessions.get(call_id, {})

    # === BRANCH: vendor outbound call ended ===
    if session_info.get("call_type") == "vendor_dispatch":
        ticket_id = session_info.get("ticket_id")
        tenant_email = session_info.get("tenant_email")
        vendor_name = session_info.get("vendor_name") or "the vendor"
        prop_name = session_info.get("property_name") or "Unknown_Property"
        flat_no = session_info.get("flat_no") or "Unknown_Flat"

        # Save the vendor-call transcript next to the existing tenant-call one
        safe_prop = prop_name.replace(" ", "_").replace("/", "-").lower()
        safe_flat = flat_no.replace(" ", "_").replace("/", "-").lower()
        ticket_dir = os.path.join(
            CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat,
            "tickets", f"ticket_{ticket_id}"
        )
        os.makedirs(ticket_dir, exist_ok=True)

        transcript_text = ""
        history = payload.get("transcript", payload.get("history", []))
        if isinstance(history, list):
            for message in history:
                role = message.get("role", "unknown")
                text = message.get("message", message.get("text", ""))
                transcript_text += f"[{role.upper()}]: {text}\n"
        else:
            transcript_text = str(history)

        transcript_path = os.path.join(ticket_dir, f"call_{call_id}_vendor_transcript.txt")
        async with aiofiles.open(transcript_path, "w", encoding="utf-8") as f:
            await f.write(transcript_text)

        # Read availability that the vendor agent wrote into master_context.next_steps
        availability: Optional[str] = None
        if prop_name != "Unknown_Property" and flat_no != "Unknown_Flat" and ticket_id:
            ctx_data = await read_master_context(prop_name, flat_no, ticket_id)
            if ctx_data:
                availability = ctx_data.get("next_steps") or ctx_data.get("suggestions")

        summary = payload.get("summary", "")
        context = await append_timeline_event(
            property_name=prop_name,
            flat_no=flat_no,
            ticket_id=ticket_id or call_id,
            event_type="vendor_call_end",
            author="system",
            description=f"Vendor call ended. Availability: {availability or 'not captured'}",
            payload={
                "call_id": call_id,
                "summary": summary,
                "vendor_name": vendor_name,
                "availability": availability,
            },
        )

        # Auto-send confirmation email to tenant
        email_status = "skipped"
        email_provider_id = None
        email_error = None
        if tenant_email and availability:
            email_subject = "Maintenance update — vendor scheduled"
            email_body = (
                f"Hello,\n\n"
                f"Good news — we've coordinated a vendor for your maintenance request.\n\n"
                f"Vendor:       {vendor_name}\n"
                f"Availability: {availability}\n"
                f"Address:      {prop_name}, flat {flat_no}\n\n"
                f"They'll attend at the time above. If anything needs to change, just reply to this email.\n\n"
                f"— HelloTheo property management"
            )
            email_result = await send_email(
                to_email=tenant_email,
                subject=email_subject,
                body=email_body,
            )
            email_status = email_result.get("status", "unknown")
            email_provider_id = email_result.get("provider_id")
            email_error = email_result.get("error")
        elif not tenant_email:
            email_error = "no tenant email on file"
        elif not availability:
            email_error = "vendor did not capture availability"

        # Append a separate timeline event for the email so it's visible in TicketDrawer.
        if ticket_id:
            email_event_desc = (
                f"Confirmation email sent to {tenant_email}"
                if email_status == "sent"
                else f"Confirmation email NOT sent ({email_error or email_status})"
            )
            context = await append_timeline_event(
                property_name=prop_name,
                flat_no=flat_no,
                ticket_id=ticket_id,
                event_type="tenant_email_sent" if email_status == "sent" else "tenant_email_failed",
                author="system",
                description=email_event_desc,
                payload={
                    "tenant_email": tenant_email,
                    "email_status": email_status,
                    "email_provider_id": email_provider_id,
                    "email_error": email_error,
                    "vendor_name": vendor_name,
                    "availability": availability,
                },
            )

        await manager.broadcast(call_id, {
            "event": "vendor_dispatch_complete",
            "ticket_id": ticket_id,
            "vendor_name": vendor_name,
            "availability": availability,
            "tenant_email": tenant_email,
            "email_status": email_status,
            "email_provider_id": email_provider_id,
            "email_error": email_error,
            "context": context,
        })

        # Clean up session
        active_call_sessions.pop(call_id, None)
        return {
            "status": "vendor_dispatch_complete",
            "ticket_id": ticket_id,
            "availability": availability,
            "email_status": email_status,
            "email_error": email_error,
        }

    # === BRANCH: tenant inbound call ended (original logic) ===
    session_info = active_call_sessions.pop(call_id, {})
    prop_name = session_info.get("property_name", "Unknown_Property")
    flat_no = session_info.get("flat_no", "Unknown_Flat")

    async with async_session_maker() as session:
        stmt = select(Ticket).where(Ticket.id == call_id)
        result = await session.execute(stmt)
        ticket = result.scalars().first()

        ticket_id = ticket.id if ticket else f"ticket_{int(datetime.utcnow().timestamp())}"

        safe_prop = prop_name.replace(" ", "_").replace("/", "-").lower()
        safe_flat = flat_no.replace(" ", "_").replace("/", "-").lower()
        ticket_dir = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "tickets", f"ticket_{ticket_id}")
        os.makedirs(ticket_dir, exist_ok=True)

        transcript_path = os.path.join(ticket_dir, f"call_{call_id}_transcript.txt")

        transcript_text = ""
        history = payload.get("transcript", payload.get("history", []))
        if isinstance(history, list):
            for message in history:
                role = message.get("role", "unknown")
                text = message.get("message", message.get("text", ""))
                transcript_text += f"[{role.upper()}]: {text}\n"
        else:
            transcript_text = str(history)

        async with aiofiles.open(transcript_path, "w", encoding="utf-8") as f:
            await f.write(transcript_text)

        summary = payload.get("summary", "No call summary provided.")
        context = await append_timeline_event(
            property_name=prop_name,
            flat_no=flat_no,
            ticket_id=ticket_id,
            event_type="call_end",
            author="system",
            description=f"Phone call ended. Summary: {summary}",
            payload={"call_id": call_id, "summary": summary, "transcript_file": f"call_{call_id}_transcript.txt"}
        )

        await manager.broadcast(call_id, {"event": "call_end", "context": context})

    return {"status": "processed", "ticket_id": ticket_id}


@app.websocket("/api/ws/calls/{call_id}")
async def websocket_endpoint(websocket: WebSocket, call_id: str):
    """WebSocket stream for dashboard to receive real-time updates of call logs."""
    await manager.connect(call_id, websocket)
    try:
        # Keep connection open
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(call_id, websocket)


@app.websocket("/api/ws/live")
async def live_websocket_endpoint(websocket: WebSocket):
    """WebSocket stream for dashboard to receive real-time updates of ALL active calls and operations."""
    await manager.connect("all", websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect("all", websocket)


@app.get("/api/calls/active")
async def get_active_calls():
    """Returns all active call sessions."""
    return active_call_sessions


@app.get("/api/tickets")
async def get_tickets():
    """Returns all tickets stored in SQLite DB with property details."""
    async with async_session_maker() as session:
        # Join Ticket and Property to fetch the property name
        stmt = (
            select(Ticket, Property.name)
            .join(Property, Ticket.property_id == Property.id)
            .order_by(Ticket.updated_at.desc())
        )
        result = await session.execute(stmt)
        tickets_with_prop = result.all()
        
        response_data = []
        for ticket, prop_name in tickets_with_prop:
            ticket_dict = ticket.dict()
            ticket_dict["property_name"] = prop_name
            response_data.append(ticket_dict)
            
        return response_data


@app.patch("/api/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, patch_data: dict):
    """
    Updates a ticket's fields (status, priority, issue_category, vendor_id, description)
    and logs a timeline event indicating what was modified.
    """
    async with async_session_maker() as session:
        stmt = select(Ticket).where(Ticket.id == ticket_id)
        result = await session.execute(stmt)
        ticket = result.scalars().first()
        
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
            
        changes = []
        if "priority" in patch_data and patch_data["priority"] is not None:
            old = ticket.priority
            new = patch_data["priority"].upper()
            if old != new:
                ticket.priority = new
                changes.append(f"priority: {old} -> {new}")
                
        if "category" in patch_data and patch_data["category"] is not None:
            old = ticket.issue_category
            new = patch_data["category"].lower()
            if old != new:
                ticket.issue_category = new
                changes.append(f"category: {old} -> {new}")
        elif "issue_category" in patch_data and patch_data["issue_category"] is not None:
            old = ticket.issue_category
            new = patch_data["issue_category"].lower()
            if old != new:
                ticket.issue_category = new
                changes.append(f"category: {old} -> {new}")
                
        if "status" in patch_data and patch_data["status"] is not None:
            old = ticket.status
            new = patch_data["status"].upper()
            if old != new:
                ticket.status = new
                changes.append(f"status: {old} -> {new}")
                
        if "vendorId" in patch_data:
            old = ticket.vendor_id
            new = patch_data["vendorId"]
            if old != new:
                ticket.vendor_id = new
                changes.append(f"vendor: {old or 'None'} -> {new or 'None'}")
        elif "vendor_id" in patch_data:
            old = ticket.vendor_id
            new = patch_data["vendor_id"]
            if old != new:
                ticket.vendor_id = new
                changes.append(f"vendor: {old or 'None'} -> {new or 'None'}")
                
        if "description" in patch_data and patch_data["description"] is not None:
            old = ticket.description
            new = patch_data["description"]
            if old != new:
                ticket.description = new
                changes.append("description updated")
                
        if changes:
            ticket.updated_at = datetime.utcnow()
            session.add(ticket)
            
            # Lookup property details to append to timeline SOT context file
            prop_stmt = select(Property).where(Property.id == ticket.property_id)
            prop_result = await session.execute(prop_stmt)
            prop = prop_result.scalars().first()
            
            if prop:
                change_desc = ", ".join(changes)
                context = await append_timeline_event(
                    property_name=prop.name,
                    flat_no=ticket.flat_no,
                    ticket_id=ticket.id,
                    event_type="ticket_update",
                    author="manager",
                    description=f"Ticket details edited: {change_desc}",
                    payload={
                        "status": ticket.status,
                        "priority": ticket.priority,
                        "issue_category": ticket.issue_category,
                        "description": ticket.description,
                        "vendor_id": ticket.vendor_id,
                        "changes": changes
                    }
                )
                # Broadcast updated context to all websocket subscribers
                await manager.broadcast(ticket_id, {"event": "context_update", "context": context})
                
        await session.commit()
        return {"status": "success", "ticket_id": ticket_id}


@app.get("/api/tickets/{ticket_id}/context")
async def get_ticket_context(ticket_id: str):
    """Reads and returns the master context file directly from filesystem using ticket ID lookup, enriched with DB details."""
    async with async_session_maker() as session:
        ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
        ticket_result = await session.execute(ticket_stmt)
        ticket = ticket_result.scalars().first()
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found in database")
            
        prop_stmt = select(Property).where(Property.id == ticket.property_id)
        prop_result = await session.execute(prop_stmt)
        prop = prop_result.scalars().first()
        if not prop:
            raise HTTPException(status_code=404, detail=f"Property not found for ticket {ticket_id}")
            
        # Get owners
        owner_link_stmt = select(Owner).join(PropertyOwnerLink).where(PropertyOwnerLink.property_id == prop.id)
        owner_link_result = await session.execute(owner_link_stmt)
        prop_owners = owner_link_result.scalars().all()
        owners_list = [{"id": o.id, "name": o.name, "email": o.email, "phone": o.phone} for o in prop_owners]
        
        # Get tenant
        tenant_details = None
        if ticket.tenant_id:
            tenant_stmt = select(Tenant).where(Tenant.id == ticket.tenant_id)
            tenant_result = await session.execute(tenant_stmt)
            tenant = tenant_result.scalars().first()
            if tenant:
                tenant_details = {
                    "id": tenant.id,
                    "name": tenant.name,
                    "phone": tenant.phone,
                    "email": tenant.email
                }
                
    context = await read_master_context(prop.name, ticket.flat_no, ticket_id)
    if not context:
        # Fallback to creating a baseline
        context = {
            "ticket_id": ticket_id,
            "property_name": prop.name,
            "flat_no": ticket.flat_no,
            "timeline": []
        }
        
    # Enrich context
    context["property_details"] = {
        "id": prop.id,
        "name": prop.name,
        "address": prop.address,
        "zipcode": prop.zipcode
    }
    context["owners"] = owners_list
    context["tenant_details"] = tenant_details
    context["created_at"] = ticket.created_at.isoformat() if ticket.created_at else None
    context["updated_at"] = ticket.updated_at.isoformat() if ticket.updated_at else None
    
    return context



@app.get("/api/tickets/{ticket_id}/transcript")
async def get_ticket_transcript(ticket_id: str):
    """Reads and returns the call transcript text from the filesystem using ticket ID lookup."""
    async with async_session_maker() as session:
        ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
        ticket_result = await session.execute(ticket_stmt)
        ticket = ticket_result.scalars().first()
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found in database")
            
        prop_stmt = select(Property).where(Property.id == ticket.property_id)
        prop_result = await session.execute(prop_stmt)
        prop = prop_result.scalars().first()
        if not prop:
            raise HTTPException(status_code=404, detail=f"Property not found for ticket {ticket_id}")
            
    safe_prop = prop.name.replace(" ", "_").replace("/", "-").lower()
    safe_flat = ticket.flat_no.replace(" ", "_").replace("/", "-").lower()
    transcript_path = os.path.join(
        CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "tickets", f"ticket_{ticket_id}", f"call_{ticket_id}_transcript.txt"
    )
    
    if not os.path.exists(transcript_path):
        fallback_path = os.path.join(
            CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "tickets", f"ticket_{ticket_id}", f"call_mock_call_999_transcript.txt"
        )
        if os.path.exists(fallback_path):
            transcript_path = fallback_path
        else:
            return {"transcript": "Transcript not available for this ticket."}
            
    async with aiofiles.open(transcript_path, "r", encoding="utf-8") as f:
        content = await f.read()
        return {"transcript": content}


@app.get("/api/vendors")
async def list_vendors(category: Optional[str] = None):
    """Return vendors, optionally filtered by category (case-insensitive)."""
    async with async_session_maker() as session:
        stmt = select(Vendor)
        if category:
            stmt = stmt.where(Vendor.category == category.strip().lower())
        result = await session.execute(stmt)
        vendors_list = result.scalars().all()
        return [
            {
                "id": v.id,
                "name": v.name,
                "phone": v.phone,
                "email": v.email,
                "category": v.category,
                "zipcode_coverage": v.zipcode_coverage,
            }
            for v in vendors_list
        ]


@app.post("/api/tickets/{ticket_id}/dispatch-vendor")
async def dispatch_vendor(ticket_id: str, payload: dict):
    """
    Place an outbound call to a vendor via the ElevenLabs Outbound Calling API
    (ElevenLabs handles the Twilio leg internally using the linked phone number).

    Body: { "vendor_id": str }
    """
    vendor_id = payload.get("vendor_id")
    if not vendor_id:
        raise HTTPException(status_code=400, detail="vendor_id is required in body")

    async with async_session_maker() as session:
        ticket_result = await session.execute(select(Ticket).where(Ticket.id == ticket_id))
        ticket = ticket_result.scalars().first()
        if not ticket:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")

        vendor_result = await session.execute(select(Vendor).where(Vendor.id == vendor_id))
        vendor = vendor_result.scalars().first()
        if not vendor:
            raise HTTPException(status_code=404, detail=f"Vendor {vendor_id} not found")

        prop_result = await session.execute(select(Property).where(Property.id == ticket.property_id))
        prop = prop_result.scalars().first()

        tenant_email: Optional[str] = None
        if ticket.tenant_id:
            tenant_result = await session.execute(select(Tenant).where(Tenant.id == ticket.tenant_id))
            tenant = tenant_result.scalars().first()
            if tenant:
                tenant_email = tenant.email

        # Snapshot ticket fields before we update (used inside the prompt template)
        prop_name = prop.name if prop else ""
        ticket_flat = ticket.flat_no
        ticket_description = ticket.description
        ticket_category = ticket.issue_category
        ticket_priority = ticket.priority

        # Patch the ticket to reflect dispatch
        ticket.vendor_id = vendor_id
        ticket.status = "DISPATCHED"
        ticket.updated_at = datetime.utcnow()
        session.add(ticket)
        await session.commit()

    # Verify ElevenLabs credentials are loaded
    agent_id = os.environ.get("ELEVENLABS_AGENT_ID")
    agent_phone_number_id = os.environ.get("ELEVENLABS_AGENT_PHONE_NUMBER_ID")
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    missing = [
        name for name, val in [
            ("ELEVENLABS_AGENT_ID", agent_id),
            ("ELEVENLABS_AGENT_PHONE_NUMBER_ID", agent_phone_number_id),
            ("ELEVENLABS_API_KEY", api_key),
        ] if not val
    ]
    if missing:
        raise HTTPException(
            status_code=500,
            detail=f"Missing ElevenLabs env vars: {', '.join(missing)}",
        )

    vendor_prompt = (
        f"You are calling {vendor.name} on behalf of HelloTheo property management. "
        f"There is a {ticket_category} issue at {prop_name}, flat {ticket_flat}: "
        f"\"{ticket_description}\" (priority: {ticket_priority}). "
        f"Greet politely, summarize the issue in one sentence, then ask when they can attend. "
        f"Once they give a time window, repeat it back to confirm, then call update_master_context "
        f"with call_id='{ticket_id}', property_name='{prop_name}', flat_no='{ticket_flat}', "
        f"description='{ticket_description}', issue_category='{ticket_category}', "
        f"priority='{ticket_priority}', status='DISPATCHED', "
        f"and next_steps='Vendor availability: <the exact time they gave>'. "
        f"Be concise — under 90 seconds total."
    )
    first_message = (
        f"Hi, this is HelloTheo property management calling about a {ticket_category} "
        f"job at {prop_name}. Do you have a quick moment?"
    )

    body = {
        "agent_id": agent_id,
        "agent_phone_number_id": agent_phone_number_id,
        "to_number": vendor.phone,
        "conversation_initiation_client_data": {
            "dynamic_variables": {
                "call_type": "vendor_dispatch",
                "ticket_id": ticket_id,
                "vendor_name": vendor.name,
                "property_name": prop_name,
                "flat_no": ticket_flat,
                "description": ticket_description,
                "category": ticket_category,
            },
            "conversation_config_override": {
                "agent": {
                    "prompt": {"prompt": vendor_prompt},
                    "first_message": first_message,
                }
            },
        },
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                "https://api.elevenlabs.io/v1/convai/twilio/outbound-call",
                headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                json=body,
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ElevenLabs request failed: {e}")

    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"ElevenLabs returned HTTP {response.status_code}: {response.text}",
        )

    data = response.json()
    conversation_id = (
        data.get("conversation_id")
        or data.get("callSid")
        or data.get("call_sid")
        or data.get("conversation", {}).get("id")
    )

    # Seed an active session keyed by the conversation_id so the post-call webhook
    # can identify this as a vendor_dispatch and trigger the tenant email.
    if conversation_id:
        active_call_sessions[conversation_id] = {
            "call_type": "vendor_dispatch",
            "ticket_id": ticket_id,
            "vendor_id": vendor_id,
            "vendor_name": vendor.name,
            "tenant_email": tenant_email,
            "property_name": prop_name,
            "flat_no": ticket_flat,
        }

    # Log timeline + broadcast to dashboard
    if prop_name:
        await append_timeline_event(
            property_name=prop_name,
            flat_no=ticket_flat,
            ticket_id=ticket_id,
            event_type="vendor_dispatch_start",
            author="manager",
            description=f"Outbound call placed to vendor {vendor.name} via ElevenLabs.",
            payload={
                "vendor_id": vendor_id,
                "vendor_phone": vendor.phone,
                "conversation_id": conversation_id,
            },
        )

    await manager.broadcast(ticket_id, {
        "event": "vendor_dispatch_start",
        "ticket_id": ticket_id,
        "vendor_name": vendor.name,
        "vendor_phone": vendor.phone,
        "conversation_id": conversation_id,
    })

    return {
        "status": "dispatched",
        "conversation_id": conversation_id,
        "ticket_id": ticket_id,
        "vendor_name": vendor.name,
        "vendor_phone": vendor.phone,
        "tenant_email": tenant_email,
    }


@app.post("/api/manager/approve")
async def manager_approve(call_id: str, status: str):
    """
    Called by Next.js dashboard when manager clicks [Approve] or [Reject].
    Updates the ApprovalRequest entry in SQLite so the blocking tool call unblocks.
    """
    if status not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be APPROVED or REJECTED")
        
    async with async_session_maker() as session:
        stmt = select(ApprovalRequest).where(ApprovalRequest.call_id == call_id, ApprovalRequest.status == "PENDING")
        result = await session.execute(stmt)
        req = result.scalars().first()
        
        if not req:
            raise HTTPException(status_code=404, detail="Pending approval request not found")
            
        req.status = status
        req.updated_at = datetime.utcnow()
        session.add(req)
        
        # Get ticket to append event
        ticket_stmt = select(Ticket).where(Ticket.id == req.ticket_id)
        ticket_result = await session.execute(ticket_stmt)
        ticket = ticket_result.scalars().first()
        
        if ticket:
            # Look up property details
            prop_stmt = select(Property).where(Property.id == ticket.property_id)
            prop_result = await session.execute(prop_stmt)
            prop = prop_result.scalars().first()
            
            if prop:
                # Update ticket status accordingly
                if status == "APPROVED":
                    ticket.status = "APPROVED"
                else:
                    ticket.status = "NEW"
                ticket.updated_at = datetime.utcnow()
                session.add(ticket)
                
                # Update context SOT file
                context = await append_timeline_event(
                    property_name=prop.name,
                    flat_no=ticket.flat_no,
                    ticket_id=ticket.id,
                    event_type="approval_response",
                    author="manager",
                    description=f"Manager response received: {status}",
                    payload={"status": ticket.status, "approval_status": status}
                )
                # Broadcast updated context
                await manager.broadcast(call_id, {"event": "approval_response", "context": context})

        await session.commit()
    return {"status": "success", "approval_status": status}


# Run command configuration
if __name__ == "__main__":
    import uvicorn
    # Start ASGI server running FastAPI (with mounted FastMCP)
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)



