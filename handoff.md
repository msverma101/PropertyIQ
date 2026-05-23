# Handoff: TenantOps — Always-On AI Maintenance Coordinator

## Purpose of this document

This document captures the full working context for continuing the first hackathon challenge:

**ElevenLabs Track — Autonomous Tenant & Vendor Operations**

The goal is to let the next agent continue immediately without needing to reconstruct prior discussion.

---

## User context

User: **Aditya Ghanashyam Ladawa**

Relevant background from uploaded resume:

- AI Engineer / AI & Processes Engineer at Brandl Nutrition.
- Experience building production automation systems.
- Built a multi-modal LLM-based AI email agent in n8n using DHL and Shopify REST APIs.
- Built demand forecasting automation using Prophet, EOQ optimization, Docker, AWS, and Looker Studio dashboards.
- Research Assistant experience with FastAPI, LangChain, IBM Docling, PDF processing, table/figure extraction, and LLM-based structured reports.
- Experience with LangGraph, Neo4j, Qdrant, RAG, LightRAG, and context-engineered agents.
- Built a previous hackathon project: **Context Engine for Buena Property Management**, ingesting 6,000+ emails and mixed-source documents into a source-backed `Context.md` map.
- Won 2nd place at HealthHack 2026 with CoNurse.
- Built SynthMotion using LangGraph, LangChain, OpenAI, Hera Motion Graphics API, and ElevenLabs.

Implication: User is strong in agentic systems, workflow automation, RAG/context engineering, structured extraction, and production-style integrations. The project should not be a generic chatbot.

---

## Original challenge text

The challenge is about tenant communication and service coordination.

Problem:

- Tenant communication is repetitive and manual.
- Maintenance requests require too much back-and-forth.
- Vendor coordination is chaotic.
- Status updates consume property manager time.

Goal:

> Design an AI-powered operations layer that automates communication, coordination, and service workflows across tenants, landlords, and vendors.

Challenge prompts:

- “What if 80% of tenant requests never needed a human?”
- “How do we coordinate vendors without back-and-forth chaos?”
- “What would a fully automated maintenance workflow look like?”

Inspiration:

- Automated workflows for repairs, inquiries, and updates.
- AI chat + voice interfaces.
- Vendor/internal team task routing.
- Status tracking and communication loops.

Bonus points:

- Real-time voice AI call handling.
- Multi-channel orchestration: email, SMS, phone.
- Sentiment detection and escalation logic.
- End-to-end resolution tracking.

Outcome vision:

> An always-on operations engine that handles communication and coordination with minimal human input.

---

## Interpretation of the challenge

The challenge is **not** asking for a simple tenant chatbot.

The expected system is an **AI operations layer** that receives tenant requests, understands them, coordinates vendors, updates tenants, escalates when needed, and tracks resolution.

The core workflow is:

```text
tenant
↓
AI intake
↓
triage
↓
property/vendor context lookup
↓
ticket creation
↓
vendor coordination
↓
tenant status update
↓
follow-up / escalation
↓
resolution confirmation
```

The project should demonstrate operational reliability, not just conversation quality.

---

## Recommended project

# TenantOps: Always-On AI Maintenance Coordinator

## One-line pitch

TenantOps answers tenant maintenance requests through voice/chat, triages the issue, coordinates the correct vendor, updates the tenant, escalates delays, and tracks the case until resolution.

## Why this is the right build

Most teams will likely build:

```text
voice chatbot + ticket creation
```

The stronger version is:

```text
voice intake
+ workflow state machine
+ vendor routing
+ status tracking
+ escalation logic
+ operations dashboard
```

This better matches the challenge’s “operations layer” and “always-on operations team” framing.

---

## Core product concept

TenantOps acts as a 24/7 AI maintenance coordinator.

It can:

1. Receive a tenant request by voice or chat.
2. Ask clarifying questions.
3. Extract structured issue details.
4. Classify urgency and sentiment.
5. Check whether the tenant already has an open/recent ticket.
6. Select the correct vendor type.
7. Contact the primary vendor.
8. If vendor does not respond, contact backup vendor.
9. Keep tenant updated.
10. Escalate to property manager if SLA is breached or sentiment is high-risk.
11. Track the request until closed.

---

## Recommended demo scenario

Use one focused scenario, not many weak ones.

# Scenario: Heating failure with delayed vendor response

## Step 1: Tenant calls

Tenant says:

```text
Hi, my heating has stopped working again. I already reported this last week and nobody came.
```

## Step 2: AI voice agent asks clarifying questions

The AI asks:

```text
Which rooms are affected?
Do you still have hot water?
Is anyone vulnerable in the apartment, such as children or elderly residents?
Can a technician access the apartment tomorrow morning or afternoon?
```

## Step 3: AI extracts structured request

Expected extracted JSON:

```json
{
  "tenant_name": "Lisa Müller",
  "property_id": "prop_berlin_001",
  "unit": "3B",
  "issue_type": "heating",
  "urgency": "high",
  "sentiment": "frustrated",
  "repeat_issue": true,
  "requires_vendor": true,
  "vendor_category": "HVAC",
  "access_permission": true,
  "preferred_time_windows": ["tomorrow afternoon"],
  "missing_info": []
}
```

## Step 4: AI checks history

Fake context:

```text
Previous ticket opened last week.
Same tenant complained twice.
Primary vendor did not confirm appointment.
SLA is at risk.
```

## Step 5: AI contacts vendor

Vendor message:

```text
High-priority heating issue at Unit 3B, Berlin. Tenant reports repeat failure. Can you attend tomorrow between 10:00–12:00 or 14:00–16:00?
```

## Step 6: Vendor response

Fake vendor response:

```text
We can come tomorrow 14:00–16:00.
```

## Step 7: AI updates tenant

Tenant update:

```text
Your heating technician is scheduled for tomorrow between 14:00 and 16:00. Your case has been marked high priority because this is a repeat issue.
```

## Step 8: Dashboard updates

Dashboard shows:

```text
Ticket: Heating failure
Tenant: Lisa Müller
Unit: 3B
Urgency: High
Sentiment: Frustrated
Vendor: Berlin HVAC GmbH
Status: Scheduled
Next action: Confirm completion after visit
Escalation risk: Medium
```

---

## Better demo twist: fallback vendor

If primary vendor does not reply within a short demo window, e.g. 30 seconds / simulated 6 hours:

```text
AI detects no vendor response
→ marks SLA risk
→ contacts backup HVAC vendor
→ notifies property manager
→ updates tenant that the issue is being escalated
```

This directly answers the prompt:

> “How do we coordinate vendors without back-and-forth chaos?”

---

## MVP feature list

Build only the following for the hackathon MVP:

1. **Voice/chat tenant intake**
   - ElevenLabs voice agent preferred.
   - Chat fallback acceptable.

2. **Issue classifier**
   - Classifies maintenance issue type.
   - Extracts tenant, property, urgency, sentiment, missing information.

3. **Ticket state machine**
   - Tracks lifecycle from intake to closure.

4. **Vendor router**
   - Maps issue type to primary and backup vendor.

5. **Vendor communication simulator**
   - For demo, vendor replies can be simulated through UI buttons, mock webhook, or fake inbox.

6. **Tenant status updater**
   - Generates tenant-facing updates.

7. **Escalation engine**
   - Escalates based on sentiment, SLA breach, repeat issue, or vendor delay.

8. **Operations dashboard**
   - Shows open tickets, statuses, escalation risk, messages, and next action.

---

## Do not build in MVP

Avoid scope creep.

Do not build these first:

```text
real SMS integration
real phone numbers
full tenant portal
full vendor marketplace
landlord accounting
real payment processing
complex OAuth for every service
multi-company SaaS permissions
mobile app
advanced RAG over thousands of documents
```

Advanced RAG and graph memory can be added later, but the hackathon demo should focus on workflow automation.

---

## Suggested architecture

```text
ElevenLabs voice agent / chat UI
        ↓
FastAPI backend
        ↓
LLM triage + structured extraction
        ↓
Postgres ticket state
        ↓
Vendor routing rules
        ↓
Vendor message simulator / webhook
        ↓
Escalation engine
        ↓
Next.js dashboard
```

Optional additions:

```text
n8n for workflow orchestration
Qdrant for document/context retrieval
Neo4j for property relationship graph
Stripe test mode for payment-related extension
```

For this challenge, Qdrant/Neo4j are optional. The demo is stronger if the workflow loop is reliable.

---

## Core data model

Recommended tables:

```sql
CREATE TABLE tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    property_id TEXT,
    unit_id TEXT,
    preferred_language TEXT
);

CREATE TABLE properties (
    id TEXT PRIMARY KEY,
    address TEXT NOT NULL,
    manager_id TEXT,
    landlord_id TEXT
);

CREATE TABLE vendors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    service_area TEXT,
    priority_rank INTEGER,
    avg_response_time_minutes INTEGER
);

CREATE TABLE maintenance_tickets (
    id TEXT PRIMARY KEY,
    tenant_id TEXT,
    property_id TEXT,
    issue_type TEXT,
    urgency TEXT,
    sentiment TEXT,
    repeat_issue BOOLEAN DEFAULT false,
    status TEXT,
    assigned_vendor_id TEXT,
    sla_deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    ticket_id TEXT,
    sender_type TEXT,
    recipient_type TEXT,
    channel TEXT,
    content TEXT,
    timestamp TIMESTAMP DEFAULT now()
);

CREATE TABLE events (
    id TEXT PRIMARY KEY,
    ticket_id TEXT,
    event_type TEXT,
    payload JSONB,
    timestamp TIMESTAMP DEFAULT now()
);
```

---

## Ticket lifecycle

Use deterministic states.

```text
NEW
→ NEEDS_INFO
→ TRIAGED
→ VENDOR_CONTACTED
→ SCHEDULED
→ IN_PROGRESS
→ RESOLVED_PENDING_CONFIRMATION
→ CLOSED
```

Escalation states:

```text
ESCALATED
MANAGER_REVIEW
BACKUP_VENDOR_CONTACTED
REOPENED
```

Important transitions:

```text
NEW + complete information → TRIAGED
NEW + missing information → NEEDS_INFO
TRIAGED + vendor selected → VENDOR_CONTACTED
VENDOR_CONTACTED + vendor confirms → SCHEDULED
VENDOR_CONTACTED + no reply after threshold → BACKUP_VENDOR_CONTACTED
SCHEDULED + completion reported → RESOLVED_PENDING_CONFIRMATION
RESOLVED_PENDING_CONFIRMATION + tenant confirms → CLOSED
RESOLVED_PENDING_CONFIRMATION + tenant rejects → REOPENED
```

---

## Escalation logic

Escalate when:

```text
tenant sentiment is angry/frustrated
tenant has contacted 3+ times
issue type is emergency
same issue is repeated
vendor does not respond within SLA
SLA deadline is close or breached
landlord approval is delayed
repair estimate exceeds threshold
```

Example deterministic rules:

```python
def should_escalate(ticket):
    if ticket.urgency == "emergency":
        return True
    if ticket.sentiment in ["angry", "frustrated"] and ticket.repeat_issue:
        return True
    if ticket.vendor_response_missing and ticket.sla_minutes_remaining < 60:
        return True
    if ticket.contact_count >= 3:
        return True
    return False
```

---

## Vendor routing logic

Issue categories and vendor mapping:

```text
heating → HVAC vendor
plumbing → plumber
electrical → electrician
lockout / lost key → locksmith
elevator → elevator company
cleaning → cleaning vendor
appliance → appliance repair
mold → property manager review + specialist
water leak → emergency plumber
```

Vendor selection should consider:

```text
category match
service area
priority rank
availability
average response time
backup vendor availability
```

For MVP, use a static JSON vendor config.

Example:

```json
{
  "heating": {
    "primary_vendor_id": "vendor_hvac_001",
    "backup_vendor_id": "vendor_hvac_002",
    "sla_hours": 6
  },
  "plumbing": {
    "primary_vendor_id": "vendor_plumber_001",
    "backup_vendor_id": "vendor_plumber_002",
    "sla_hours": 4
  }
}
```

---

## Synthetic dataset needed

No real dataset is required.

Create fake data:

```text
20 tenants
10 properties
15 vendors
100 maintenance tickets
300 messages
20 landlord approval rules
```

Minimum seed data for demo:

```text
Tenant:
- Lisa Müller
- Unit 3B
- Property: Berlin / Musterstraße 12

Issue:
- Heating stopped working again
- Repeat issue
- High frustration

Vendor:
- Primary: Berlin HVAC GmbH
- Backup: WärmeFix24

History:
- Ticket from last week
- Vendor failed to confirm
- Tenant already sent 2 previous messages
```

Example SLA rules:

```text
water leak → 2 hours
heating failure → 6 hours
lockout → 1 hour
appliance repair → 3 days
cosmetic issue → 7 days
```

---

## Core AI tasks

Use AI only where it creates leverage.

## AI task 1: structured extraction

Input:

```text
My heating is broken again and nobody came last week.
```

Output:

```json
{
  "issue_type": "heating",
  "urgency": "high",
  "repeat_issue": true,
  "sentiment": "frustrated",
  "missing_info": ["access_permission", "preferred_time"]
}
```

## AI task 2: next-action decision

Input:

```json
{
  "issue_type": "heating",
  "urgency": "high",
  "vendor_response": "none",
  "hours_since_vendor_contacted": 6,
  "tenant_sentiment": "frustrated"
}
```

Output:

```json
{
  "next_action": "escalate_and_contact_backup_vendor",
  "reason": "High-priority repeat heating issue with no vendor response"
}
```

## AI task 3: communication drafting

Tenant message:

```text
We have escalated your heating issue and contacted a backup technician because the first vendor has not confirmed availability.
```

Vendor message:

```text
High-priority heating issue at Unit 3B. Tenant reports repeat failure. Please confirm availability today.
```

Property manager message:

```text
High-priority repeat heating issue requires review. Primary vendor has not responded and backup vendor has been contacted.
```

---

## Suggested app screens

## 1. Intake screen

Shows live transcript or chat.

Fields:

```text
tenant
property
issue type
urgency
sentiment
missing info
confidence
```

## 2. Operations dashboard

Cards:

```text
Open tickets
High priority
Waiting for vendor
Escalated
Scheduled today
SLA risk
```

## 3. Ticket detail page

Sections:

```text
summary
tenant info
property info
status timeline
messages
vendor assignment
next action
approval buttons
```

## 4. Vendor simulator

Simple panel with buttons:

```text
Accept appointment
Reject appointment
No response
Request more info
Complete repair
```

## 5. Manager approval panel

Buttons:

```text
Approve escalation
Contact backup vendor
Send tenant update
Mark resolved
Reopen ticket
```

---

## Recommended stack

Frontend:

```text
Next.js
Tailwind
shadcn/ui
```

Backend:

```text
FastAPI
Postgres
SQLAlchemy or SQLModel
Pydantic
```

AI/workflows:

```text
LangGraph or simple deterministic workflow engine
OpenAI / Gemini / Claude for extraction and drafting
ElevenLabs for voice agent
```

Infrastructure:

```text
Docker Compose
ngrok for local webhook testing
```

Optional:

```text
n8n if user wants visual workflows
Qdrant for semantic context
Neo4j for property/vendor relationship graph
```

---

## Recommended build order

## Day 1: backend + seed data

- Create FastAPI app.
- Create Postgres schema.
- Seed tenants, vendors, properties, tickets.
- Implement ticket creation endpoint.
- Implement vendor routing config.

## Day 2: AI extraction + state machine

- Add LLM structured extraction.
- Add issue classification.
- Add status transitions.
- Add escalation rules.

## Day 3: dashboard

- Build Next.js dashboard.
- Add ticket list.
- Add ticket detail timeline.
- Add vendor simulator buttons.

## Day 4: ElevenLabs / voice

- Connect voice intake.
- Route transcript to FastAPI.
- Return clarifying questions or confirmation.
- Save transcript as messages.

## Day 5: demo polish

- Add one perfect heating-failure flow.
- Add fallback vendor flow.
- Add clean README.
- Add demo script.
- Record video.

---

## Demo script

Use this exact flow:

1. Open dashboard.
2. Show no critical issues or a few background tickets.
3. Start tenant voice call.
4. Tenant says heating failed again.
5. AI asks clarifying questions.
6. AI creates ticket and classifies as high priority.
7. Dashboard updates live.
8. AI contacts primary vendor.
9. Simulate no vendor response.
10. Escalation engine contacts backup vendor.
11. Backup vendor accepts appointment.
12. AI updates tenant.
13. Ticket timeline shows full trace.
14. Property manager dashboard shows resolved next step.

Core phrase for judges:

```text
This is not only a voice bot. It is a workflow state machine for property operations. The AI handles conversation, but the system owns coordination, escalation, and resolution tracking.
```

---

## Success criteria

The MVP is successful if it shows:

```text
tenant request enters system
AI extracts structured issue
AI asks missing questions
ticket is created
vendor is selected
vendor is contacted
tenant receives updates
no-response case escalates
dashboard tracks full lifecycle
```

---

## What to emphasize in judging

Emphasize:

```text
80% request deflection
vendor coordination without back-and-forth
always-on voice intake
clear state machine
sentiment + escalation
human-in-the-loop control
end-to-end traceability
```

Avoid emphasizing:

```text
generic chatbot
generic RAG
database complexity
abstract agent architecture
```

---

## Possible project names

Best:

```text
TenantOps
```

Alternatives:

```text
FixFlow AI
PropOps Voice
Maintainer AI
VendorLoop
RepairOps
AlwaysOn PM
```

Recommended final:

```text
TenantOps: Always-On AI Maintenance Coordinator
```

---

## Open decisions for next agent

The next agent should help decide:

1. Whether to use ElevenLabs conversational AI directly or only TTS/STT around a custom backend.
2. Whether to use LangGraph or a simpler deterministic state machine.
3. Whether vendor communication should be simulated through UI or email/webhook.
4. Whether to include landlord approval in MVP or leave it as a demo extension.
5. Whether to integrate n8n or keep workflow logic in FastAPI.
6. Whether to add Stripe test payments as an optional second-track feature later.

Recommended choices:

```text
Use deterministic workflow engine first.
Use ElevenLabs for voice intake if setup time allows.
Simulate vendor responses in UI.
Skip landlord approval unless time remains.
Skip Stripe for this first challenge.
```

---

## Critical implementation warning

Do not let the project become “agent does everything.”

Use this split:

```text
LLM:
- understand tenant request
- extract fields
- draft messages
- explain reasoning

Rules/state machine:
- ticket statuses
- SLA transitions
- vendor routing
- escalation triggers
- approval gates
```

This makes the system reliable and easier to demo.

---

## Final recommendation

Build:

# TenantOps: Always-On AI Maintenance Coordinator

It should demonstrate:

```text
Voice/chat tenant intake
→ structured triage
→ ticket creation
→ vendor routing
→ vendor coordination
→ tenant updates
→ fallback vendor escalation
→ resolution tracking dashboard
```

This is the best fit for the first challenge because it directly addresses the core problem: repetitive tenant communication and chaotic vendor coordination.
