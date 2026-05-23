# TenantOps: Always-On AI Maintenance Coordinator

TenantOps is an AI-powered operations layer that automates property management, tenant communication, defect triage, and vendor coordination. Built for the **ElevenLabs Track — Autonomous Tenant & Vendor Operations**, it deflects repetitive communication while keeping human managers in the loop for approvals.

Rather than a simple conversational chatbot, **TenantOps** integrates a deterministic state machine, real-time WebSocket sync, and a FastMCP model context protocol server to coordinate dispatches end-to-end.

---

## 🚀 Key Features

* **🎙️ Always-On Voice Intake**: Integrates ElevenLabs Conversational AI to greet tenants dynamically, triage defects, and extract structured issue parameters.
* **📂 Enriched Database Context**: FastMCP dynamically pulls co-owners cards (names, emails, phones), tenant contact cards, property zipcodes, and physical context logs.
* **⏱️ Background Tool Auditing**: Every background action the AI takes (e.g., `read_context`, `search_vendors`, `request_manager_approval`, `send_notification_email`) is printed in real-time on the dashboard timeline audit trail.
* **🚨 Manager-in-the-Loop Approval**: Securely holds vendor dispatches until the property manager approves them in one click from the dashboard or directly in the terminal console.
* **✉️ Automated Notifications**: Automatically drafts and dispatches structured work orders to the primary vendor and sends CC emails to all property owners and updates to the tenant.

---

## 🏗️ Architecture

```text
       ElevenLabs Voice Agent / Phone Line
                      │
                      ▼
               FastAPI Backend  ◄──►  SQLite (SQLModel)
         (SSE FastMCP & WebSockets)
                      │
                      ├──────────────────────────┐
                      ▼                          ▼
               Vite Frontend             Physical Contexts
            (TanStack Start UI)        (Properties & Timelines)
```

---

## 🛠️ Tech Stack

* **Frontend**: React (TypeScript), TanStack Start, Tailwind CSS, Lucide icons, Sonner notifications.
* **Backend**: FastAPI, SQLModel (SQLite), FastMCP (Model Context Protocol), WebSockets (real-time broadcasting).
* **Environment Management**: Python venv, Pip/UV package managers.

---

## 🏁 Quick Start Guide

Follow these steps to spin up the entire TenantOps environment locally:

### 1. Clone & Setup Virtual Environment
Activate the pre-configured virtual environment and install backend dependencies:
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
uv pip install -r pyproject.toml
```

### 2. Start the Backend (FastAPI + SSE MCP)
Run the ASGI server to boot up the FastAPI REST API and mount the SSE MCP server under `/mcp`:
```bash
python backend/app.py
```
* **Backend API**: `http://localhost:8000`
* **SSE MCP Connection URL**: `http://localhost:8000/mcp/sse`

### 3. Start the Frontend Dashboard (Vite)
Open a new terminal window, navigate to the root directory, and launch the dashboard:
```bash
npm run dev
# or using bun
bun run dev
```
* **Dashboard URL**: `http://localhost:5173`

### 4. Tunnel Port 8000 via Ngrok (For ElevenLabs & Webhooks)
To connect the voice agent to your local environment, expose port 8000 to the internet:
```bash
ngrok http 8000
```
This will generate a forwarding URL (e.g., `https://tabasco-sincere-reseal.ngrok-free.dev`).

Use this tunnel URL to update your integration endpoints:
* **SSE MCP URL**: `https://tabasco-sincere-reseal.ngrok-free.dev/mcp/sse`
* **ElevenLabs Caller Lookup Webhook**: `https://tabasco-sincere-reseal.ngrok-free.dev/api/caller-lookup`
* **ElevenLabs Call Ended Webhook**: `https://tabasco-sincere-reseal.ngrok-free.dev/api/calls/{call_id}/ended`

---

## 🔌 Registered MCP Configuration
Your local developer environment is registered with the following Model Context Protocol configurations in your `mcp_config.json` for seamless agent interaction:

```json
{
  "mcpServers": {
    "hellotheo-ops": {
      "command": "/home/aditya-ladawa/Aditya/y_projects/tv_ops/.venv/bin/fastmcp",
      "args": [
        "run",
        "/home/aditya-ladawa/Aditya/y_projects/tv_ops/backend/mcp_tools.py"
      ],
      "env": {
        "PYTHONPATH": "/home/aditya-ladawa/Aditya/y_projects/tv_ops/backend"
      }
    }
  }
}
```

---

## 🚨 ElevenLabs Voice Agent Prompt Protocol
When setting up your voice agent on ElevenLabs, configure your **System Prompt** with this robust, tool-calling execution protocol:

> [!IMPORTANT]
> **COMPULSORY FIRST STEP:** At the absolute start of any incoming call, before requesting details, asking questions, or calling other tools, the agent **MUST** invoke the `read_context` tool with the provided `call_id` to retrieve tenant, property, co-owner, and ticket information.

### Operational Sequence:
1. **Greet the caller** by name using the retrieved lookup details.
2. ** Clarify the problem** (nature of the leak/heating issue, access permission, presence of vulnerable occupants).
3. **Register/Update details** using `update_master_context` to log the defect details in the DB and filesystem.
4. **Search and find** the appropriate trade specialist using `search_vendors` with category and zipcode.
5. **Request manager authorization** via `request_manager_approval` for any high-cost or emergency dispatches.
6. **Dispatch & Notify** the co-owners, vendor, and tenant using `send_notification_email`.
