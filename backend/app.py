import os
import json
import asyncio
import aiofiles
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

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
async def caller_lookup(phone: str, call_id: Optional[str] = None):
    """
    Called by ElevenLabs Twilio integration upon incoming call.
    Resolves who is calling and returns dynamic greeting.
    """
    # Clean phone number (remove spaces and ensure '+' prefix)
    phone = phone.strip()
    if phone and not phone.startswith("+"):
        phone = "+" + phone
    
    # Generate fallback call_id if not supplied
    resolved_call_id = call_id or f"call_{int(datetime.utcnow().timestamp())}"
    
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
    """
    # 1. Retrieve session info
    session_info = active_call_sessions.pop(call_id, {})
    prop_name = session_info.get("property_name", "Unknown_Property")
    flat_no = session_info.get("flat_no", "Unknown_Flat")
    
    # Look up active ticket for this call
    async with async_session_maker() as session:
        stmt = select(Ticket).where(Ticket.id == call_id)
        result = await session.execute(stmt)
        ticket = result.scalars().first()
        
        ticket_id = ticket.id if ticket else f"ticket_{int(datetime.utcnow().timestamp())}"
        
        # 2. Save transcript to property-unit folder
        safe_prop = prop_name.replace(" ", "_").replace("/", "-").lower()
        safe_flat = flat_no.replace(" ", "_").replace("/", "-").lower()
        ticket_dir = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "tickets", f"ticket_{ticket_id}")
        os.makedirs(ticket_dir, exist_ok=True)
        
        transcript_path = os.path.join(ticket_dir, f"call_{call_id}_transcript.txt")
        
        transcript_text = ""
        # ElevenLabs sends conversation history in structured formats
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

        # 3. Append final timeline event
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
        
        # Broadcast finished state to dashboard WebSocket
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



