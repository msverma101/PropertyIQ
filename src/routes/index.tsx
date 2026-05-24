import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useRef, useState, useEffect } from "react";
import { Sparkles, Building2 } from "lucide-react";
import { toast } from "sonner";
import {
  seedTickets,
  tenants,
  vendors,
  type Ticket,
  type Category,
  type Priority,
  type Status,
} from "@/lib/tenantops-data";
import { LiveCallPanel, type LiveCallState } from "@/components/tenantops/LiveCallPanel";
import { TicketsTable } from "@/components/tenantops/TicketsTable";
import { ApprovalModal, type ApprovalContext } from "@/components/tenantops/ApprovalModal";
import { TicketDrawer } from "@/components/tenantops/TicketDrawer";

export const Route = createFileRoute("/")({
  component: Index,
  head: () => ({
    meta: [
      { title: "PropertyIQ — Live maintenance dashboard" },
      {
        name: "description",
        content:
          "Monitor AI-handled tenant maintenance calls and approve vendor dispatches in one click.",
      },
    ],
  }),
});

const IDLE: LiveCallState = { active: false, step: 0 };

const ELEVENLABS_AGENT_ID = "agent_0601ksayj2zhf5dbdq6me1kvs7cf";
const ELEVENLABS_WIDGET_SCRIPT = "https://unpkg.com/@elevenlabs/convai-widget-embed";

function Index() {
  const [tickets, setTickets] = useState<Ticket[]>(seedTickets);
  const [call, setCall] = useState<LiveCallState>(IDLE);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [approval, setApproval] = useState<{
    open: boolean;
    ctx: ApprovalContext | null;
    ticketId?: string;
    dispatchVendorId?: string;
  }>({ open: false, ctx: null });
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);
  const autoPoppedTickets = useRef<Set<string>>(new Set());
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  // Inject the ElevenLabs Convai widget script once on mount.
  useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.querySelector(`script[src="${ELEVENLABS_WIDGET_SCRIPT}"]`)) return;
    const script = document.createElement("script");
    script.src = ELEVENLABS_WIDGET_SCRIPT;
    script.async = true;
    script.type = "text/javascript";
    document.body.appendChild(script);
  }, []);

  const clearTimers = () => {
    timers.current.forEach((t) => clearTimeout(t));
    timers.current = [];
  };

  async function fetchTickets() {
    try {
      const res = await fetch("http://localhost:8000/api/tickets");
      if (res.ok) {
        const data = await res.json();
        const mapped = data.map((t: any) => ({
          id: t.id,
          tenantId: t.tenant_id || "unknown",
          property: t.property_name || "Musterstraße 12",
          flat: t.flat_no || "Unit",
          category: (t.issue_category ? (t.issue_category.charAt(0).toUpperCase() + t.issue_category.slice(1)) : "Plumbing") as Category,
          description: t.description || "",
          priority: t.priority as Priority,
          status: t.status as Status,
          vendorId: t.vendor_id || undefined,
          createdAt: t.created_at || new Date().toISOString(),
          timeline: []
        }));
        setTickets(mapped);
      }
    } catch (err) {
      console.error("Failed to fetch tickets", err);
    }
  }

  async function handleSelectTicket(ticket: Ticket | null) {
    if (!ticket) {
      setSelected(null);
      return;
    }
    
    setSelected(ticket);
    
    try {
      const contextRes = await fetch(`http://localhost:8000/api/tickets/${ticket.id}/context`);
      let timelineEvents = ticket.timeline;
      let enrichedDetails = {};
      if (contextRes.ok) {
        const contextData = await contextRes.json();
        timelineEvents = (contextData.timeline || []).map((e: any) => ({
          at: e.timestamp,
          label: e.description || e.type,
          detail: e.author ? `By ${e.author}` : undefined
        }));
        
        enrichedDetails = {
          propertyDetails: contextData.property_details,
          owners: contextData.owners,
          tenantDetails: contextData.tenant_details,
          updatedAt: contextData.updated_at
        };
      }

      const transcriptRes = await fetch(`http://localhost:8000/api/tickets/${ticket.id}/transcript`);
      let transcriptText = ticket.transcript;
      if (transcriptRes.ok) {
        const transcriptData = await transcriptRes.json();
        transcriptText = transcriptData.transcript;
      }

      setSelected({
        ...ticket,
        timeline: timelineEvents,
        transcript: transcriptText,
        ...enrichedDetails
      });
    } catch (err) {
      console.error("Failed to fetch ticket context/transcript", err);
    }
  }

  useEffect(() => {
    fetchTickets();

    const ws = new WebSocket("ws://localhost:8000/api/ws/live");
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("WebSocket event received:", data);
      
      if (data.event === "call_start") {
        setCall({
          active: true,
          step: 0,
          tenant: {
            id: data.caller_type === "tenant" ? "t1" : "unknown",
            name: data.caller_name || "Guest",
            initials: data.caller_name ? data.caller_name.split(" ").map((n: string) => n[0]).join("") : "G",
            property: data.property_name || "Unknown",
            flat: data.flat_no || "Unknown"
          },
          description: "",
          confidence: 0
        });
        toast.info(`Inbound call connected: ${data.caller_name || "Guest"}`);
      } else if (data.event === "context_update" || data.event === "approval_request" || data.event === "approval_response" || data.event === "approval_timeout") {
        const ctx = data.context;
        if (ctx) {
          setCall((prev) => {
            if (!prev.active) return prev;
            
            const priority = (ctx.priority || prev.priority) as Priority;
            const category = (ctx.issue_category ? (ctx.issue_category.charAt(0).toUpperCase() + ctx.issue_category.slice(1)) : prev.category) as Category;
            const description = ctx.description || prev.description;
            
            let step = prev.step || 0;
            if (data.event === "context_update") step = 3;
            if (data.event === "approval_request") step = 4;
            
            return {
              ...prev,
              step,
              priority,
              category,
              description,
              confidence: 96
            };
          });

          fetchTickets();

          if (data.event === "approval_request") {
            setApproval({
              open: true,
              ticketId: ctx.ticket_id,
              ctx: {
                tenantName: ctx.caller_name || "Tenant",
                category: ctx.issue_category || "Plumbing",
                summary: ctx.description || "leak",
                vendorName: "RohrBlitz Berlin",
                estimate: 180
              }
            });
          } else if (data.event === "approval_response" || data.event === "approval_timeout") {
            setApproval({ open: false, ctx: null });
            toast(`Manager Approval Status: ${ctx.status || "CLOSED"}`);
          } else if (data.event === "context_update") {
            console.log("[autoPop] context_update received", {
              ticket_id: ctx.ticket_id,
              issue_category: ctx.issue_category,
              description: ctx.description,
              alreadyPopped: ctx.ticket_id ? autoPoppedTickets.current.has(ctx.ticket_id) : "n/a",
            });
            // Auto-pop the dispatch approval modal once the agent has captured a
            // full ticket (ticket_id + issue_category + description). Guard against
            // duplicate pops if the agent updates the same ticket twice.
            if (
              ctx.ticket_id &&
              ctx.issue_category &&
              ctx.description &&
              !autoPoppedTickets.current.has(ctx.ticket_id)
            ) {
              console.log("[autoPop] all conditions met, scheduling openDispatchModal");
              autoPoppedTickets.current.add(ctx.ticket_id);
              // Reset the LiveCallPanel — the agent has captured enough; the call
              // is effectively done from the dashboard's perspective.
              setCall(IDLE);
              const catLower = String(ctx.issue_category).toLowerCase();
              const catCapitalized = catLower.charAt(0).toUpperCase() + catLower.slice(1);
              // caller_name is in the most recent timeline entry's payload
              const callerName: string | undefined =
                ctx.caller_name
                || (Array.isArray(ctx.timeline) && ctx.timeline.length
                    ? ctx.timeline[ctx.timeline.length - 1]?.payload?.caller_name
                    : undefined)
                || undefined;
              const stub: Ticket = {
                id: ctx.ticket_id,
                tenantId: "",
                property: ctx.property_name || "",
                flat: ctx.flat_no || "",
                category: catCapitalized as Category,
                description: ctx.description || "",
                priority: (ctx.priority || "MEDIUM") as Priority,
                status: (ctx.status || "NEW") as Status,
                createdAt: new Date().toISOString(),
                timeline: [],
                ...(callerName
                  ? { tenantDetails: { id: "", name: callerName, phone: "", email: "" } }
                  : {}),
              };
              // Small delay so any concurrent state updates settle first.
              setTimeout(() => openDispatchModal(stub), 800);
            }
          }
        }
      } else if (data.event === "call_end") {
        setCall(IDLE);
        toast.success("Call ended and transcript offloaded.");
        fetchTickets();

        // Auto-open the dispatch approval modal if the agent captured enough context.
        const ctx = data.context;
        if (ctx?.ticket_id && ctx?.issue_category) {
          const catLower = String(ctx.issue_category).toLowerCase();
          const catCapitalized = catLower.charAt(0).toUpperCase() + catLower.slice(1);
          const stub: Ticket = {
            id: ctx.ticket_id,
            tenantId: "",
            property: ctx.property_name || "",
            flat: ctx.flat_no || "",
            category: catCapitalized as Category,
            description: ctx.description || "",
            priority: (ctx.priority || "MEDIUM") as Priority,
            status: (ctx.status || "NEW") as Status,
            createdAt: new Date().toISOString(),
            timeline: [],
          };
          // Small delay so the call_end toast settles before the modal animates in.
          setTimeout(() => openDispatchModal(stub), 600);
        }
      } else if (data.event === "vendor_dispatch_start") {
        toast.info(`Calling ${data.vendor_name}...`, {
          description: `Outbound call placed via ElevenLabs.`,
        });
      } else if (data.event === "vendor_dispatch_complete") {
        const emailOk = data.email_status === "sent";
        if (emailOk && data.availability) {
          toast.success(`Email sent to ${data.tenant_email || "tenant"}`, {
            description: [
              `Vendor: ${data.vendor_name}`,
              `Availability: ${data.availability}`,
              data.email_provider_id ? `Resend id: ${data.email_provider_id}` : null,
            ]
              .filter(Boolean)
              .join("  |  "),
            duration: 12000,
          });
        } else if (data.availability) {
          toast.warning(`Vendor confirmed but email failed`, {
            description: data.email_error || "Check Resend logs.",
            duration: 12000,
          });
        } else {
          toast.error(`Vendor call ended without availability`, {
            description: data.email_error || "No follow-up email sent.",
          });
        }
        fetchTickets();
      }
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected. Retrying in 3s...");
    };

    return () => {
      ws.close();
    };
  }, []);

  const simulate = useCallback(() => {
    if (call.active) return;
    clearTimers();
    const tenant = tenants[0]; // Lisa Chen
    const vendor = vendors[0]; // QuickFix Berlin
    const fullDesc =
      "Active leak under the kitchen sink — water pooling on the floor, shut-off valve not holding.";

    // Step 0: call connects (idle metadata)
    setCall({ active: true, tenant, step: 0, confidence: 0 });

    // Step 1: description types in
    const typeStart = 800;
    const perChar = 18;
    timers.current.push(
      setTimeout(() => {
        setCall((c) => ({ ...c, step: 1, description: "" }));
        for (let i = 1; i <= fullDesc.length; i++) {
          timers.current.push(
            setTimeout(() => {
              setCall((c) => ({ ...c, description: fullDesc.slice(0, i) }));
            }, i * perChar)
          );
        }
      }, typeStart)
    );

    const afterType = typeStart + fullDesc.length * perChar;

    // Step 2: category
    timers.current.push(
      setTimeout(() => setCall((c) => ({ ...c, step: 2, category: "Plumbing" })), afterType + 500)
    );
    // Step 3: priority
    timers.current.push(
      setTimeout(() => setCall((c) => ({ ...c, step: 3, priority: "CRITICAL" })), afterType + 1300)
    );
    // Step 4: confidence ramp
    timers.current.push(
      setTimeout(() => setCall((c) => ({ ...c, step: 4, confidence: 96 })), afterType + 2100)
    );

    // Step 5: create ticket + open approval modal
    timers.current.push(
      setTimeout(() => {
        const id = `TKT-${2042}`;
        const now = new Date().toISOString();
        const newTicket: Ticket = {
          id,
          tenantId: tenant.id,
          property: tenant.property,
          flat: tenant.flat,
          category: "Plumbing",
          description: fullDesc,
          priority: "CRITICAL",
          status: "PENDING_APPROVAL",
          createdAt: now,
          timeline: [
            { at: now, label: "Call received", detail: `Tenant ${tenant.name} via AI line` },
            { at: now, label: "AI categorized", detail: "Plumbing · CRITICAL (96%)" },
            { at: now, label: "Pending manager approval" },
          ],
          transcript: `Tenant: Hi, there's water everywhere under my kitchen sink.\nAI: I'm sorry to hear that. Have you been able to shut the water off?\nTenant: I tried the valve but it's still leaking...\nAI: Understood — I'm escalating this as critical and contacting a plumber now.`,
        };
        setTickets((prev) => [newTicket, ...prev.filter((t) => t.id !== id)]);
        setApproval({
          open: true,
          ticketId: id,
          ctx: {
            tenantName: tenant.name,
            category: "Plumbing",
            summary: "kitchen leak",
            vendorName: vendor.name,
            estimate: vendor.estimate,
          },
        });
      }, afterType + 2900)
    );
  }, [call.active]);

  const closeCall = () => {
    clearTimers();
    setCall(IDLE);
  };

  async function approveTicket(id: string) {
    try {
      const res = await fetch(`http://localhost:8000/api/manager/approve?call_id=${id}&status=APPROVED`, {
        method: "POST"
      });
      if (res.ok) {
        toast.success("Ticket approved successfully.");
        fetchTickets();
        
        setTimeout(() => {
          fetchTickets();
          toast.success("SMS sent to tenant", {
            description: "Vendor dispatch confirmed.",
          });
        }, 2000);
      } else {
        toast.error("Failed to approve ticket on backend.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to connect to backend for approval.");
    }
  }

  async function rejectTicket(id: string) {
    try {
      const res = await fetch(`http://localhost:8000/api/manager/approve?call_id=${id}&status=REJECTED`, {
        method: "POST"
      });
      if (res.ok) {
        toast.success("Ticket rejected successfully.");
        fetchTickets();
      } else {
        toast.error("Failed to reject ticket on backend.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to connect to backend for rejection.");
    }
  }

  async function updateTicket(id: string, patch: Partial<Ticket>) {
    try {
      const res = await fetch(`http://localhost:8000/api/tickets/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(patch)
      });
      if (res.ok) {
        toast.success("Ticket updated successfully.");
        fetchTickets();
        
        if (selected && selected.id === id) {
          handleSelectTicket({ ...selected, ...patch });
        }
      } else {
        toast.error("Failed to update ticket on backend.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to connect to backend to update ticket.");
    }
  }

  async function openDispatchModal(ticket: Ticket) {
    const cat = String(ticket.category || "").toLowerCase();
    if (!cat) {
      toast.error("Ticket has no category — set one before dispatching.");
      return;
    }
    try {
      const res = await fetch(`http://localhost:8000/api/vendors?category=${encodeURIComponent(cat)}`);
      if (!res.ok) {
        toast.error("Failed to load vendors from backend.");
        return;
      }
      const list: any[] = await res.json();
      if (!list.length) {
        toast.error(`No ${cat} vendors available.`);
        return;
      }
      const v = list[0];
      const summary = (ticket.description || "").slice(0, 80) || `${cat} issue`;
      setApproval({
        open: true,
        ticketId: ticket.id,
        dispatchVendorId: v.id,
        ctx: {
          tenantName: ticket.tenantDetails?.name || "Tenant",
          category: String(ticket.category || "Plumbing"),
          summary,
          vendorName: v.name,
          estimate: 180,
        },
      });
    } catch (err) {
      console.error(err);
      toast.error("Network error fetching vendors.");
    }
  }

  async function dispatchVendor(ticketId: string, vendorId: string) {
    try {
      const res = await fetch(`http://localhost:8000/api/tickets/${ticketId}/dispatch-vendor`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vendor_id: vendorId }),
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(`Outbound call placed to ${data.vendor_name}`, {
          description: `Conversation ID: ${data.conversation_id ?? "(pending)"}`,
        });
        fetchTickets();
      } else {
        const text = await res.text();
        toast.error("Dispatch failed", { description: text });
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to reach backend for dispatch.");
    }
  }

  const onApprove = async () => {
    const id = approval.ticketId!;
    const vendorId = approval.dispatchVendorId;
    setApproval({ open: false, ctx: null });
    closeCall();
    if (vendorId) {
      await dispatchVendor(id, vendorId);
    } else {
      await approveTicket(id);
    }
  };

  const onCancel = async () => {
    const id = approval.ticketId!;
    setApproval({ open: false, ctx: null });
    closeCall();
    try {
      const res = await fetch(`http://localhost:8000/api/manager/approve?call_id=${id}&status=REJECTED`, {
        method: "POST"
      });
      if (res.ok) {
        toast("Decision deferred", { description: "Ticket marked as REJECTED." });
        fetchTickets();
      } else {
        toast.error("Failed to reject ticket on backend.");
      }
    } catch (err) {
      console.error(err);
      toast.error("Failed to connect to backend to reject.");
    }
  };

  const selectedVendor = selected ? vendors.find((v) => v.id === selected.vendorId) : undefined;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card/60 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-md bg-primary text-primary-foreground">
              <Building2 className="h-4 w-4" />
            </div>
            <div>
              <h1 className="text-sm font-semibold tracking-tight text-foreground">PropertyIQ</h1>
              <p className="text-xs text-muted-foreground">AI-handled maintenance · live operations</p>
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <LiveCallPanel state={call} />

        <div>
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold text-foreground">Tickets</h2>
            <p className="text-xs text-muted-foreground">{tickets.length} total · click a row for details</p>
          </div>
          <TicketsTable
            tickets={tickets}
            vendors={vendors}
            onSelect={handleSelectTicket}
            selectedId={selected?.id}
            onApproveTicket={approveTicket}
            onRejectTicket={rejectTicket}
            onUpdateTicket={updateTicket}
          />
        </div>
      </main>

      <ApprovalModal open={approval.open} ctx={approval.ctx} onApprove={onApprove} onCancel={onCancel} />
      <TicketDrawer
        ticket={selected}
        vendor={selectedVendor}
        onClose={() => setSelected(null)}
        onDispatch={(t) => openDispatchModal(t)}
      />

      {/* ElevenLabs Convai widget — floating mic button, bottom-right.
          Only render after mount so SSR-rendered HTML stays empty
          (avoids hydration mismatch with the custom element). */}
      {mounted && (
        // @ts-expect-error custom element from @elevenlabs/convai-widget-embed
        <elevenlabs-convai agent-id={ELEVENLABS_AGENT_ID}></elevenlabs-convai>
      )}
    </div>
  );
}
