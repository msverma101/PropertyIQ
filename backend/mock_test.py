import sys
import asyncio
import httpx
from mcp import ClientSession
from mcp.client.sse import sse_client

async def run_simulation():
    print("\n" + "="*60)
    print("🚀 STARTING HELLOTHEO MOCK INTEGRATION TEST")
    print("="*60 + "\n")

    # Determine base URL from command line arguments or default to localhost:8000
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1].rstrip("/")
        print(f"🔗 Testing against custom base URL: {base_url}")
    else:
        print(f"🔗 Testing against default base URL: {base_url}")

    call_id = "mock_call_999"
    tenant_phone = "+4917636766245" # Max Müller
    
    # 1. Simulate twilio/elevenlabs call initiation (GET /api/caller-lookup)
    lookup_url = f"{base_url}/api/caller-lookup"
    print(f"1. Simulating inbound call lookup from {tenant_phone}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(lookup_url, params={"phone": tenant_phone, "call_id": call_id})
        if response.status_code != 200:
            print(f"❌ Lookup failed with status: {response.status_code}")
            return
        
        data = response.json()
        print(f"   [SUCCESS] Matched: {data.get('caller_name')} ({data.get('caller_type')})")
        print(f"   [AGENT GREETING]: \"{data.get('conversation_config_override', {}).get('agent', {}).get('first_message')}\"\n")

    # 2. Establish native MCP connection over SSE
    sse_url = f"{base_url}/mcp/sse"
    print(f"2. Connecting to MCP SSE Server at {sse_url} ...")
    try:
        async with sse_client(sse_url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as mcp_session:
                await mcp_session.initialize()
                print("   [SUCCESS] Connected to MCP server. Listing tools...")
                
                tools_list = await mcp_session.list_tools()
                print("   [TOOLS FOUND]:", [t.name for t in tools_list.tools], "\n")

                 # 3. COMPULSORY: Read context first
                print("3. Agent calls read_context first (Compulsory)...")
                read_result_1 = await mcp_session.call_tool(
                    "read_context",
                    {
                        "call_id": call_id
                    }
                )
                print(f"   [RESULT]:\n{read_result_1.content[0].text}\n")

                # 4. Simulate Agent updating the defect context (update_master_context)
                print("4. Agent logs defect details in context database...")
                context_result = await mcp_session.call_tool(
                    "update_master_context",
                    {
                        "call_id": call_id,
                        "description": "Kitchen pipe burst. Active leak flooding floor.",
                        "priority": "CRITICAL",
                        "issue_category": "plumbing",
                        "status": "NEW",
                        "next_steps": "Dispatch RohrBlitz Berlin plumber for flooding repair."
                    }
                )
                print(f"   [RESULT]: {context_result.content[0].text}\n")

                # 4.5. Read context again to verify suggestions update
                print("4.5. Agent reads context again to check updated next steps/suggestions...")
                read_result_2 = await mcp_session.call_tool(
                    "read_context",
                    {
                        "call_id": call_id
                    }
                )
                print(f"   [RESULT]:\n{read_result_2.content[0].text}\n")

                # 5. Agent searches for plumbers (search_vendors)
                print("5. Agent searches for plumbing vendors covering zipcode 10115...")
                vendor_result = await mcp_session.call_tool(
                    "search_vendors",
                    {
                        "category": "plumbing",
                        "zipcode": "10115"
                    }
                )
                print(f"   [RESULT]:\n{vendor_result.content[0].text}\n")

                # 6. Agent requests emergency manager approval (request_manager_approval)
                print("6. Agent requests manager authorization for plumber dispatch...")
                print("   ⚠️  ATTENTION: Please switch to your backend Uvicorn terminal and type 'y' to approve.")
                
                approval_result = await mcp_session.call_tool(
                    "request_manager_approval",
                    {
                        "call_id": call_id,
                        "request_details": "Dispatch RohrBlitz Berlin plumber for kitchen flooding repair. Est: €180."
                    }
                )
                print(f"   [RESULT]: {approval_result.content[0].text}\n")

                # 7. Agent sends work order email confirmation (send_notification_email)
                print("7. Agent emails co-owners and vendor...")
                email_result = await mcp_session.call_tool(
                    "send_notification_email",
                    {
                        "ticket_id": call_id,
                        "recipient_type": "owner",
                        "subject": "Work Order Approved: Kitchen Flooding at Musterstraße 12",
                        "body": "Manager Hans Schmidt approved plumber RohrBlitz Berlin to repair kitchen leak. Co-owners notified."
                    }
                )
                print(f"   [RESULT]: {email_result.content[0].text}\n")

    except Exception as e:
        print(f"❌ MCP Tool Execution failed: {e}")
        return

    # 8. Call ended offload transcript
    print("8. Simulating call hangup and transcript offload...")
    ended_url = f"{base_url}/api/calls/{call_id}/ended"
    mock_payload = {
        "transcript": [
            {"role": "user", "text": "Hi, I have a massive leak under the kitchen sink."},
            {"role": "agent", "text": "I see you are at Musterstraße 12. Let me request plumber approval."},
            {"role": "user", "text": "Thanks, it's flooding."},
            {"role": "agent", "text": "The manager approved, RohrBlitz Berlin is on the way."}
        ],
        "summary": "Tenant reported plumbing leak, manager authorized dispatch of RohrBlitz Berlin."
    }
    
    async with httpx.AsyncClient() as client:
        end_resp = await client.post(ended_url, json=mock_payload)
        if end_resp.status_code == 200:
            print("   [SUCCESS] Transcript saved successfully.")
        else:
            print(f"   [FAILED] Call ended failed with status: {end_resp.status_code}")

    print("\n" + "="*60)
    print("🎉 MOCK TEST SIMULATION COMPLETED SUCCESSFULLY!")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_simulation())
