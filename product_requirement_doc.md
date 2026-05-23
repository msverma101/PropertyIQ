# Product Requirement Document (PRD)
## Project: HelloTheo TenantOps — Always-On AI Maintenance Coordinator Dashboard

---

## 1. Product Overview & Purpose
HelloTheo's TenantOps is a 24/7 AI-powered operations layer that automates defect and maintenance issue communication, coordination, and resolution tracking. The core of the system is an ElevenLabs AI voice assistant (connected via Twilio) that converses with tenants, owners, and vendors.

This document describes the **HelloTheo Admin Dashboard**, a real-time web application built with **Next.js (React)**, **TailwindCSS**, and **Lucide Icons**. The dashboard allows property managers to monitor active voice calls, approve/reject maintenance authorizations in real time, view historical defect ticket logs, and browse property-centric context trails.

---

## 2. Core UI/UX & Design Aesthetic
To align with HelloTheo's premium digital brand, the interface should feel premium, dynamic, and modern:
* **Color Palette**: Dark mode first. Sleek charcoal backgrounds (`#0B0F19`), rich border strokes, and vibrant accents (Emerald green for active calls/success, Amber for pending approvals, Blue for general status, Rose/Red for critical urgency).
* **Styling Style**: Glassmorphic panels (semi-transparent backdrops with light border borders and subtle blur filters).
* **Typography**: Clean sans-serif fonts (e.g. Inter or Outfit) with strong hierarchy and generous padding.
* **Micro-animations**: Glowing pulse effects on the active call icon, animated waveform grids, and smooth transitions on card expands.

---

## 3. Page Structure & Features

The dashboard is structured as a single-page app or a tabbed router with the following main modules:

### A. Live Call Monitoring & Waveform Dashboard
This is the primary viewport when a phone call is actively in progress.
1. **Active Call Alert**: A sticky overlay banner or glowing top card that appears as soon as a WebSocket connection opens for an active `call_id`.
2. **The Waveform Visualizer**: A digital wave animation indicating the ElevenLabs agent is talking to a tenant.
3. **Structured Live Metadata Card**: Updates dynamically as the call proceeds (received via WebSocket payloads). It displays:
   * **Caller Name & Avatar**: e.g., "Lisa Müller" with a "Tenant" badge.
   * **Caller Address & Location**: e.g., "Musterstraße 12 / Apt 3B".
   * **Extracted Defect Details**: Live typing/summary of the issue (e.g., "Water leaking from under kitchen sink, getting worse.").
   * **Urgency & Priority Badges**: e.g., "CRITICAL" or "HIGH".
   * **Category**: e.g., "Plumbing".

### B. Human-in-the-Loop (HITL) Authorization Console
When the AI agent invokes the `request_manager_approval` tool on the call, the dashboard must immediately trigger an override modal or flashing notification panel.
1. **Approval Panel Elements**:
   * **Alert Header**: "ACTION REQUIRED: Emergency Plumber Authorization Request".
   * **Context Description**: "Tenant Lisa Müller reports an active kitchen leak. Plumber RohrBlitz Berlin is available for dispatch. Cost estimate: €180. Approve dispatch?"
   * **Action Buttons**:
     * **[APPROVE]** (Vibrant Green): Sends `POST /api/manager/approve?call_id=X&status=APPROVED` to the backend.
     * **[REJECT]** (Vibrant Red/Gray): Sends `POST /api/manager/approve?call_id=X&status=REJECTED`.
2. **Countdown Timer**: A circular or horizontal loading bar indicating a **10-second countdown**. If the manager does not click in time, the status automatically shifts to timeout and the modal fades.

### C. Defect Tickets Table & Kanban Queue
Displays all active and historical maintenance issues tracked in the database.
1. **Grid Table Columns**:
   * **Ticket ID**: Monospaced ID string.
   * **Property & Flat**: e.g., "Musterstraße 12 (Apt 3B)".
   * **Issue Category & Description**: e.g., "Plumbing: Kitchen Sink Leak".
   * **Priority Badge**: Urgency levels (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) styled with distinct warning colors.
   * **Status Badge**: e.g., `NEW`, `PENDING_APPROVAL`, `APPROVED`, `DISPATCHED`, `RESOLVED`, `CLOSED`.
   * **Assigned Vendor**: Name of the matched technician (if assigned).
   * **Date Created / Last Update**: Date format.
2. **Filter & Search Bar**: Filter by property address, ticket priority, or category.

### D. Chronological Property Context & Audit Trail Viewer
Clicking on any ticket opens the **Master Context Viewer**, which displays the chronological history of the defect parsed directly from the property's filesystem `master_context.json` file.
1. **Interactive Timeline Logs**:
   * **Phone Logs**: Highlights when calls started, ended, and shows the full transcripts (`call_<sid>_transcript.txt`) in an expandable sheet.
   * **Emails Log**: Shows when work orders were emailed to vendors (e.g., HVAC dispatch confirmation) or replies were received.
   * **Audit Log**: System-logged entries (e.g., "SLA Deadline created", "Priority changed to Critical").
2. **Interactive Management Panel**:
   * Dropdown to manually change ticket status.
   * Dropdown to assign or re-route to a backup vendor.

---

## 4. API & Real-time Integration Contract

The Next.js dashboard communicates with the FastAPI/FastMCP backend (`http://localhost:8000`) using standard REST requests and WebSocket streams.

### 1. Fetching All Tickets
* **Method & URL**: `GET /api/tickets`
* **Response Payload (JSON Array)**:
  ```json
  [
    {
      "id": "call_twilio_sid_99",
      "property_id": "prop_001",
      "flat_no": "Apt 3B",
      "tenant_id": "tenant_001",
      "vendor_id": null,
      "status": "NEW",
      "priority": "HIGH",
      "issue_category": "plumbing",
      "description": "Kitchen pipe leaking",
      "created_at": "2026-05-23T13:00:00Z",
      "updated_at": "2026-05-23T13:00:00Z"
    }
  ]
  ```

### 2. Fetching Property Context
* **Method & URL**: `GET /api/tickets/{ticket_id}/context?property_name={prop_name}&flat_no={flat_no}`
* **Response Payload (Master Context JSON)**:
  ```json
  {
    "ticket_id": "call_twilio_sid_99",
    "property_name": "Musterstraße 12",
    "flat_no": "Apt 3B",
    "status": "NEW",
    "priority": "HIGH",
    "issue_category": "plumbing",
    "description": "Kitchen pipe leaking",
    "timeline": [
      {
        "timestamp": "2026-05-23T13:00:00Z",
        "type": "call_update",
        "author": "agent",
        "description": "Ticket details updated by AI agent.",
        "payload": {
          "status": "NEW",
          "priority": "HIGH",
          "issue_category": "plumbing"
        }
      }
    ]
  }
  ```

### 3. Manager Approval Dispatch
* **Method & URL**: `POST /api/manager/approve?call_id={call_id}&status={APPROVED|REJECTED}`
* **Response**: `{"status": "success", "approval_status": "APPROVED"}`

### 4. WebSocket Live Stream
* **URL**: `ws://localhost:8000/api/ws/calls/{call_id}`
* **Event Payloads**:
  * **Context Update**: `{ "event": "context_update", "context": { ...master_context... } }`
  * **Approval Request**: `{ "event": "approval_request", "context": { ...master_context... } }`
  * **Call End**: `{ "event": "call_end", "context": { ...master_context... } }`
