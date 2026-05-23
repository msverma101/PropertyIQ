import os
import json
import asyncio
import sys
import aiofiles
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastmcp import FastMCP
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
from shared import async_session_maker, active_call_sessions, manager

# 1. Initialize FastMCP
mcp = FastMCP("HelloTheo Operations")

# Helper for async stdin reading
async def async_input(prompt: str) -> str:
    """Read a line from stdin asynchronously without blocking the main event loop."""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    loop = asyncio.get_running_loop()
    line = await loop.run_in_executor(None, sys.stdin.readline)
    return line.strip().lower()


# --- FastMCP Tools ---

@mcp.tool()
async def read_context(
    call_id: str,
    property_name: Optional[str] = None,
    flat_no: Optional[str] = None
) -> str:
    """
    COMPULSORY FIRST TOOL CALL.
    Locates and reads all context, database info, property address, owner emails, and ticket history
    interconnected with this call, property, and flat.
    Also returns next steps and suggestions for the AI agent.
    """
    # 1. Retrieve caller details from active session
    session_info = active_call_sessions.get(call_id, {})
    
    resolved_prop = property_name or session_info.get("property_name")
    resolved_flat = flat_no or session_info.get("flat_no")
    
    if resolved_prop and resolved_flat:
        await append_timeline_event(
            property_name=resolved_prop,
            flat_no=resolved_flat,
            ticket_id=call_id,
            event_type="read_context",
            author="agent",
            description="AI Agent invoked tool: 'read_context' to retrieve property and owner details."
        )
        # Broadcast changes to dashboard
        await manager.broadcast(call_id, {"event": "context_update", "context": await read_master_context(resolved_prop, resolved_flat, call_id)})

    caller_name = session_info.get("caller_name", "Unknown Caller")
    caller_type = session_info.get("caller_type", "unknown")
    phone = session_info.get("phone")

    # Start compiling output
    output = f"=== CONTEXT FOR CALL {call_id} ===\n"
    output += f"Caller: {caller_name} ({caller_type})\n"
    if phone:
        output += f"Caller Phone: {phone}\n"

    # Try to locate property in DB if we have its name
    async with async_session_maker() as session:
        prop = None
        flat = None
        
        if resolved_prop:
            prop_stmt = select(Property).where(Property.name == resolved_prop)
            prop_result = await session.execute(prop_stmt)
            prop = prop_result.scalars().first()
            
            if prop and resolved_flat:
                flat_stmt = select(Flat).where(Flat.property_id == prop.id, Flat.flat_no == resolved_flat)
                flat_result = await session.execute(flat_stmt)
                flat = flat_result.scalars().first()

        # If flat not found yet, but we have tenant info, try resolving from tenant
        tenant_id = session_info.get("tenant_id")
        if not flat and tenant_id:
            flat_stmt = select(Flat).where(Flat.tenant_id == tenant_id)
            flat_result = await session.execute(flat_stmt)
            flat = flat_result.scalars().first()
            if flat:
                prop_stmt = select(Property).where(Property.id == flat.property_id)
                prop_result = await session.execute(prop_stmt)
                prop = prop_result.scalars().first()

        # If we successfully located property and/or flat, print details
        if prop:
            output += f"\nProperty: {prop.name}\n"
            output += f"Address: {prop.address} (Zipcode: {prop.zipcode})\n"
            
            # Retrieve all owners
            owner_stmt = select(Owner).join(PropertyOwnerLink).where(PropertyOwnerLink.property_id == prop.id)
            owner_result = await session.execute(owner_stmt)
            owners = owner_result.scalars().all()
            output += f"Owners:\n"
            for o in owners:
                output += f"  - {o.name} (Email: {o.email}, Phone: {o.phone})\n"
        else:
            output += f"\nProperty: {resolved_prop or 'Not Specified'}\n"
            output += "Owners: None found in database.\n"

        if flat:
            output += f"Unit/Flat: {flat.flat_no} (Rented: {'Yes' if flat.is_rented else 'No'})\n"
            
            # Look up tenant if any
            if flat.tenant_id:
                tenant_stmt = select(Tenant).where(Tenant.id == flat.tenant_id)
                tenant_result = await session.execute(tenant_stmt)
                t = tenant_result.scalars().first()
                if t:
                    output += f"Tenant in Unit: {t.name} (Email: {t.email})\n"
        else:
            output += f"Unit/Flat: {resolved_flat or 'Not Specified'}\n"

        # Now locate tickets in DB associated with this property/flat
        tickets_list = []
        if prop:
            ticket_query = select(Ticket).where(Ticket.property_id == prop.id)
            if flat:
                ticket_query = ticket_query.where(Ticket.flat_no == flat.flat_no)
            ticket_result = await session.execute(ticket_query)
            tickets_list = ticket_result.scalars().all()

        output += f"\n--- Interconnected Tickets (Database) ---\n"
        if tickets_list:
            for tk in tickets_list:
                output += f"  * Ticket {tk.id}: status={tk.status}, priority={tk.priority}, category={tk.issue_category}, description='{tk.description}'\n"
        else:
            output += "  No tickets found in database.\n"

        # Look up local physical file context store as well
        output += f"\n--- Physical File Context Store ---\n"
        context_data = None
        if resolved_prop and resolved_flat:
            safe_prop = resolved_prop.replace(" ", "_").replace("/", "-").lower()
            safe_flat = resolved_flat.replace(" ", "_").replace("/", "-").lower()
            
            # 1. Property details
            prop_details_path = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "property_details.json")
            if os.path.exists(prop_details_path):
                output += "  [File] property_details.json: Found\n"
                
            # 2. Flat details
            flat_details_path = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "flat_details.json")
            if os.path.exists(flat_details_path):
                output += "  [File] flat_details.json: Found\n"

            # 3. Master context file (for active or specified ticket)
            ticket_file_dir = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "tickets")
            if os.path.exists(ticket_file_dir):
                ticket_dirs = [d for d in os.listdir(ticket_file_dir) if d.startswith("ticket_")]
                if ticket_dirs:
                    output += f"  [Folder] Ticket Directories Found: {', '.join(ticket_dirs)}\n"
                    context_data = await read_master_context(resolved_prop, resolved_flat, call_id)
                    if context_data:
                        output += "  [File] master_context.json for this call: Found\n"
                        output += f"         Current Status: {context_data.get('status')}\n"
                        output += f"         Current Priority: {context_data.get('priority')}\n"
                        output += f"         Current Description: '{context_data.get('description', '')}'\n"
                        
                        # Show timeline summary
                        timeline = context_data.get("timeline", [])
                        if timeline:
                            output += "         Timeline Events:\n"
                            for event in timeline:
                                output += f"           - [{event.get('timestamp')}] {event.get('type')} by {event.get('author')}: {event.get('description')}\n"
                else:
                    output += "  [Folder] No ticket directories found in context store.\n"
            else:
                output += "  [Folder] No tickets path found in context store.\n"
        else:
            output += "  [Physical Store] Missing property_name or flat_no, cannot query filesystem context.\n"

    # Define next steps / suggestions dynamically based on state
    output += f"\n--- Next Steps & Suggestions ---\n"
    
    # Check if suggestions are stored explicitly
    if context_data and (context_data.get("next_steps") or context_data.get("suggestions")):
        stored_suggestions = context_data.get("next_steps") or context_data.get("suggestions")
        output += f"  [Stored Suggestions]: {stored_suggestions}\n"
    else:
        output += "  [Dynamic Suggestions]:\n"
        if context_data:
            status = context_data.get("status", "NEW")
            category = context_data.get("issue_category", "unknown")
            if status == "NEW":
                output += f"    1. Call 'search_vendors' with category '{category}' and property zipcode to find a vendor.\n"
                output += "    2. Call 'request_manager_approval' to dispatch the vendor.\n"
            elif status == "PENDING_APPROVAL":
                output += "    1. Wait for manager approval. Do not dispatch vendor yet.\n"
            elif status == "APPROVED":
                output += "    1. Plumber dispatch approved. Call 'send_notification_email' to notify primary owner, co-owners, and vendor.\n"
        else:
            output += "    1. Ask the tenant to describe the maintenance problem.\n"
            output += "    2. Call 'update_master_context' to create the ticket and record the defect details.\n"

    return output


@mcp.tool()
async def update_master_context(
    call_id: str,
    description: str,
    priority: str,
    issue_category: str,
    status: str = "NEW",
    property_name: Optional[str] = None,
    flat_no: Optional[str] = None,
    next_steps: Optional[str] = None
) -> str:
    """
    Updates the master context log file and DB ticket for the active call.
    Must be called during the conversation when new defect details are gathered.
    """
    # 1. Retrieve caller details from active session
    session_info = active_call_sessions.get(call_id, {})
    
    # Fallback to arguments if call registration is missing or empty
    resolved_prop = property_name or session_info.get("property_name")
    resolved_flat = flat_no or session_info.get("flat_no")
    tenant_id = session_info.get("tenant_id")
    
    if not resolved_prop or not resolved_flat:
        return "Error: Property address and flat number are required to log context. Please ask the caller for these details."

    async with async_session_maker() as session:
        # Look up property ID in SQLite
        prop_stmt = select(Property).where(Property.name == resolved_prop)
        prop_result = await session.execute(prop_stmt)
        prop = prop_result.scalars().first()
        
        if not prop:
            # Create a mock property if we don't have it (e.g. guest calls and provides address)
            prop = Property(id=f"prop_{int(datetime.utcnow().timestamp())}", name=resolved_prop, address=resolved_prop, zipcode="10000")
            session.add(prop)
            await session.commit()
            await session.refresh(prop)
            # Link to default owner
            link = PropertyOwnerLink(owner_id="owner_001", property_id=prop.id)
            session.add(link)
            await session.commit()
            
        # Get or create ticket
        ticket_stmt = select(Ticket).where(Ticket.id == call_id)
        ticket_result = await session.execute(ticket_stmt)
        ticket = ticket_result.scalars().first()
        
        is_new_ticket = False
        if not ticket:
            is_new_ticket = True
            ticket = Ticket(
                id=call_id,
                property_id=prop.id,
                flat_no=resolved_flat,
                tenant_id=tenant_id,
                status=status,
                priority=priority.upper(),
                issue_category=issue_category.lower(),
                description=description
            )
            session.add(ticket)
        else:
            ticket.status = status
            ticket.priority = priority.upper()
            ticket.issue_category = issue_category.lower()
            ticket.description = description
            ticket.updated_at = datetime.utcnow()
            session.add(ticket)
            
        await session.commit()
        await session.refresh(ticket)
        
        # Write to filesystem context store
        event_desc = "AI Agent invoked tool: 'update_master_context' - Ticket created." if is_new_ticket else "AI Agent invoked tool: 'update_master_context' - Ticket details updated."
        context = await append_timeline_event(
            property_name=resolved_prop,
            flat_no=resolved_flat,
            ticket_id=ticket.id,
            event_type="call_update",
            author="agent",
            description=event_desc,
            payload={
                "status": ticket.status,
                "priority": ticket.priority,
                "issue_category": ticket.issue_category,
                "description": ticket.description,
                "caller_name": session_info.get("caller_name", "Guest"),
                "next_steps": next_steps
            }
        )
        
        # Broadcast changes to dashboard
        await manager.broadcast(call_id, {"event": "context_update", "context": context})
        
    return f"Successfully updated context store and ticket in DB: {ticket.id}"


@mcp.tool()
async def search_vendors(category: str, zipcode: str, call_id: Optional[str] = None) -> str:
    """
    Search SQLite DB for active maintenance vendors matching a service category and zipcode.
    """
    # Resolve active call ID if not supplied
    resolved_call_id = call_id
    if not resolved_call_id and active_call_sessions:
        resolved_call_id = list(active_call_sessions.keys())[0]
        
    if resolved_call_id:
        session_info = active_call_sessions.get(resolved_call_id, {})
        resolved_prop = session_info.get("property_name")
        resolved_flat = session_info.get("flat_no")
        if resolved_prop and resolved_flat:
            context = await append_timeline_event(
                property_name=resolved_prop,
                flat_no=resolved_flat,
                ticket_id=resolved_call_id,
                event_type="search_vendors",
                author="agent",
                description=f"AI Agent invoked tool: 'search_vendors' for category '{category}' and zipcode '{zipcode}'."
            )
            # Broadcast update
            await manager.broadcast(resolved_call_id, {"event": "context_update", "context": context})

    async with async_session_maker() as session:
        stmt = select(Vendor).where(Vendor.category == category.lower())
        result = await session.execute(stmt)
        vendors = result.scalars().all()
        
        matched_vendors = []
        for vendor in vendors:
            # Check if property zipcode is covered by vendor
            coverage = [z.strip() for z in vendor.zipcode_coverage.split(",")]
            if zipcode in coverage:
                matched_vendors.append(vendor)
                
        if not matched_vendors:
            return f"No vendors found for category '{category}' covering zipcode '{zipcode}'."
            
        response_text = f"Found {len(matched_vendors)} matching vendor(s):\n"
        for v in matched_vendors:
            response_text += f"- {v.name} (Phone: {v.phone}, Email: {v.email})\n"
            
        return response_text


@mcp.tool()
async def request_manager_approval(call_id: str, request_details: str) -> str:
    """
    Submits a defect authorization request to the terminal.
    Prompts the console operator to approve (y) or reject (n) the request.
    """
    async with async_session_maker() as session:
        # Check if ticket exists
        ticket_stmt = select(Ticket).where(Ticket.id == call_id)
        ticket_result = await session.execute(ticket_stmt)
        ticket = ticket_result.scalars().first()
        
        if not ticket:
            return "Error: Cannot request approval. No active ticket found. Please call update_master_context first."
            
        # Update ticket status to PENDING_APPROVAL
        ticket.status = "PENDING_APPROVAL"
        session.add(ticket)
        
        # Create approval request entry in DB
        req_id = f"req_{int(datetime.utcnow().timestamp())}"
        req = ApprovalRequest(
            id=req_id,
            call_id=call_id,
            ticket_id=ticket.id,
            details=request_details,
            status="PENDING"
        )
        session.add(req)
        await session.commit()
        
        # Get property details to update context file
        prop_stmt = select(Property).where(Property.id == ticket.property_id)
        prop_result = await session.execute(prop_stmt)
        prop = prop_result.scalars().first()
        
        if prop:
            # Append approval request to context timeline
            context = await append_timeline_event(
                property_name=prop.name,
                flat_no=ticket.flat_no,
                ticket_id=ticket.id,
                event_type="approval_request",
                author="agent",
                description=f"AI Agent invoked tool: 'request_manager_approval' - Authorization requested: {request_details}",
                payload={"status": "PENDING_APPROVAL", "request_details": request_details}
            )
            # Broadcast update (for WebSocket subscribers)
            await manager.broadcast(call_id, {"event": "approval_request", "context": context})

    # Prompt the console operator in the terminal
    banner = (
        "\n"
        "==============================================================\n"
        "🚨 [ACTION REQUIRED - HELLOTHEO MANAGER APPROVAL REQUEST]\n"
        f"📞 Call ID: {call_id}\n"
        f"📋 Details: {request_details}\n"
        "--------------------------------------------------------------\n"
        "👉 Approve this request? (Type 'y' for Yes, 'n' for No) [20s limit]: "
    )
    
    status = "PENDING"
    try:
        # Wait for terminal input (20s timeout)
        user_choice = await asyncio.wait_for(async_input(banner), timeout=20.0)
        
        if user_choice == "y":
            status = "APPROVED"
        else:
            status = "REJECTED"
            
    except asyncio.TimeoutError:
        status = "TIMEOUT"
        print("\n⏳ Manager approval request timed out (20s).")

    # Update state in DB and context store
    async with async_session_maker() as session:
        # Load request and ticket
        req_stmt = select(ApprovalRequest).where(ApprovalRequest.call_id == call_id).order_by(ApprovalRequest.created_at.desc())
        req_result = await session.execute(req_stmt)
        db_req = req_result.scalars().first()
        if db_req:
            db_req.status = status
            db_req.updated_at = datetime.utcnow()
            session.add(db_req)
            
        ticket_stmt = select(Ticket).where(Ticket.id == call_id)
        ticket_result = await session.execute(ticket_stmt)
        ticket = ticket_result.scalars().first()
        
        if ticket:
            if status == "APPROVED":
                ticket.status = "APPROVED"
            else:
                ticket.status = "NEW" # Revert or leave open
            ticket.updated_at = datetime.utcnow()
            session.add(ticket)
            
            # Save timeline event
            prop_stmt = select(Property).where(Property.id == ticket.property_id)
            prop_result = await session.execute(prop_stmt)
            prop = prop_result.scalars().first()
            
            if prop:
                event_desc = f"Manager approved request." if status == "APPROVED" else (f"Manager rejected request." if status == "REJECTED" else "Approval request timed out.")
                context = await append_timeline_event(
                    property_name=prop.name,
                    flat_no=ticket.flat_no,
                    ticket_id=ticket.id,
                    event_type="approval_response" if status != "TIMEOUT" else "approval_timeout",
                    author="manager",
                    description=event_desc,
                    payload={"status": ticket.status, "approval_status": status}
                )
                # Broadcast updated context
                await manager.broadcast(call_id, {"event": "approval_response", "context": context})

        await session.commit()
        
    if status == "APPROVED":
        return "APPROVED: The request has been authorized by the manager."
    elif status == "REJECTED":
        return "REJECTED: The request was denied by the manager."
    else:
        return "TIMEOUT: The manager has not responded. Please inform the caller we have escalated the issue for later review."


# @mcp.tool()
# async def get_latest_communications(property_name: str, flat_no: str) -> str:
#     """
#     Retrieve communication history and logs for a specific property unit.
#     """
#     safe_prop = property_name.replace(" ", "_").replace("/", "-").lower()
#     safe_flat = flat_no.replace(" ", "_").replace("/", "-").lower()
#     
#     # Path to flat details
#     flat_details_path = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "flat_details.json")
#     
#     if not os.path.exists(flat_details_path):
#         return f"No records found for property '{property_name}' flat '{flat_no}'."
#         
#     async with aiofiles.open(flat_details_path, "r", encoding="utf-8") as f:
#         flat_data = json.loads(await f.read())
#         
#     tenant = flat_data.get("tenant", {})
#     output = f"Flat Records for {property_name} - Unit {flat_no}:\n"
#     output += f"- Current Tenant: {tenant.get('name', 'N/A')} (Phone: {tenant.get('phone', 'N/A')})\n"
#     output += f"- Status: Active Lease\n"
#     
#     # Search for existing tickets in this directory
#     tickets_dir = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "tickets")
#     if os.path.exists(tickets_dir):
#         tickets = os.listdir(tickets_dir)
#         output += f"- Past Ticket Logs Found: {len(tickets)}\n"
#         for t_dir in tickets:
#             mc_path = os.path.join(tickets_dir, t_dir, "master_context.json")
#             if os.path.exists(mc_path):
#                 async with aiofiles.open(mc_path, "r", encoding="utf-8") as f:
#                     mc_data = json.loads(await f.read())
#                     output += f"  * Ticket {mc_data.get('ticket_id')}: status={mc_data.get('status')}, category={mc_data.get('issue_category')}, description='{mc_data.get('description')}'\n"
#     else:
#         output += "- Past Ticket Logs Found: 0\n"
#         
#     return output


@mcp.tool()
async def send_notification_email(
    ticket_id: str,
    recipient_type: str,
    subject: str,
    body: str
) -> str:
    """
    Sends a simulated email notification regarding a maintenance ticket.
    For owners: if the property has multiple co-owners, it emails the primary owner (TO) and CCs the co-owners.
    """
    async with async_session_maker() as session:
        # Get ticket to find the property
        ticket_stmt = select(Ticket).where(Ticket.id == ticket_id)
        ticket_result = await session.execute(ticket_stmt)
        ticket = ticket_result.scalars().first()
        
        if not ticket:
            return f"Error: Ticket with ID {ticket_id} not found."
            
        # Get property details
        prop_stmt = select(Property).where(Property.id == ticket.property_id)
        prop_result = await session.execute(prop_stmt)
        prop = prop_result.scalars().first()
        
        if not prop:
            return f"Error: Associated property not found for ticket {ticket_id}."

        to_email = ""
        cc_emails = []
        recipient_name = ""

        if recipient_type.lower() == "owner":
            # Retrieve all co-owners linked to this property
            owner_stmt = select(Owner).join(PropertyOwnerLink).where(PropertyOwnerLink.property_id == prop.id)
            owner_result = await session.execute(owner_stmt)
            owners = owner_result.scalars().all()
            
            if not owners:
                return "Error: No owners linked to this property."
                
            # Primary owner is the first one, co-owners are in CC
            to_email = owners[0].email
            recipient_name = owners[0].name
            if len(owners) > 1:
                cc_emails = [o.email for o in owners[1:]]
                
        elif recipient_type.lower() == "tenant":
            if not ticket.tenant_id:
                return "Error: No tenant associated with this ticket."
            tenant_stmt = select(Tenant).where(Tenant.id == ticket.tenant_id)
            tenant_result = await session.execute(tenant_stmt)
            tenant = tenant_result.scalars().first()
            if not tenant:
                return "Error: Tenant record not found."
            to_email = tenant.email
            recipient_name = tenant.name
            
        elif recipient_type.lower() == "vendor":
            if not ticket.vendor_id:
                return "Error: No vendor associated with this ticket."
            vendor_stmt = select(Vendor).where(Vendor.id == ticket.vendor_id)
            vendor_result = await session.execute(vendor_stmt)
            vendor = vendor_result.scalars().first()
            if not vendor:
                return "Error: Vendor record not found."
            to_email = vendor.email
            recipient_name = vendor.name
            
        else:
            return f"Error: Invalid recipient type '{recipient_type}'. Must be 'owner', 'tenant', or 'vendor'."

        # Build email structure for log/audit
        email_payload = {
            "to": to_email,
            "cc": cc_emails,
            "recipient_name": recipient_name,
            "subject": subject,
            "body": body,
            "sent_at": datetime.utcnow().isoformat()
        }
        
        # Log to physical files under properties/<prop>/flats/<flat>/tickets/ticket_<id>/
        safe_prop = prop.name.replace(" ", "_").replace("/", "-").lower()
        safe_flat = ticket.flat_no.replace(" ", "_").replace("/", "-").lower()
        ticket_dir = os.path.join(CONTEXT_STORE_DIR, "properties", safe_prop, "flats", safe_flat, "tickets", f"ticket_{ticket_id}")
        os.makedirs(ticket_dir, exist_ok=True)
        
        email_log_filename = f"email_{recipient_type}_{int(datetime.utcnow().timestamp())}.json"
        email_log_path = os.path.join(ticket_dir, email_log_filename)
        
        async with aiofiles.open(email_log_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(email_payload, indent=2))
            
        # Append timeline event to the master context
        cc_str = f" (CC: {', '.join(cc_emails)})" if cc_emails else ""
        event_desc = f"AI Agent invoked tool: 'send_notification_email' - Email sent to {recipient_type} {recipient_name} <{to_email}>{cc_str} with subject: '{subject}'"
        await append_timeline_event(
            property_name=prop.name,
            flat_no=ticket.flat_no,
            ticket_id=ticket.id,
            event_type="email_sent",
            author="system",
            description=event_desc,
            payload={"email_log_file": email_log_filename, "recipient_type": recipient_type}
        )

        # Broadcast the updated timeline to the dashboard WebSocket
        await manager.broadcast(ticket.id, {
            "event": "email_sent",
            "email": email_payload
        })

        # Print a highly-visible mock email box directly to the console terminal
        cc_display = ", ".join(cc_emails) if cc_emails else "None"
        email_banner = (
            "\n"
            "┌──────────────────────────────────────────────────────────┐\n"
            "│ ✉️  SIMULATED EMAIL SENT (OUTBOUND NOTIFICATION)          │\n"
            "├──────────────────────────────────────────────────────────┤\n"
            f"│ TO:      {to_email:<47} │\n"
            f"│ CC:      {cc_display:<47} │\n"
            f"│ SUBJECT: {subject:<47} │\n"
            "├──────────────────────────────────────────────────────────┤\n"
            "│ BODY:                                                    │\n"
        )
        for line in body.split("\n"):
            # Line wrap for console display
            words = line.split(" ")
            current_line = "│   "
            for word in words:
                if len(current_line) + len(word) + 1 > 55:
                    email_banner += f"{current_line:<58}│\n"
                    current_line = "│   " + word
                else:
                    if current_line == "│   ":
                        current_line += word
                    else:
                        current_line += " " + word
            email_banner += f"{current_line:<58}│\n"
            
        email_banner += (
            "└──────────────────────────────────────────────────────────┘\n"
        )
        print(email_banner)
        
        return f"Email successfully sent to {to_email}" + (f" (CC'd: {', '.join(cc_emails)})" if cc_emails else "")
