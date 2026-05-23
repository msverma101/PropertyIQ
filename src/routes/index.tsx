import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useRef, useState } from "react";
import { Sparkles, Building2 } from "lucide-react";
import { toast } from "sonner";
import {
  seedTickets,
  tenants,
  vendors,
  type Ticket,
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

function Index() {
  const [tickets, setTickets] = useState<Ticket[]>(seedTickets);
  const [call, setCall] = useState<LiveCallState>(IDLE);
  const [selected, setSelected] = useState<Ticket | null>(null);
  const [approval, setApproval] = useState<{ open: boolean; ctx: ApprovalContext | null; ticketId?: string }>({
    open: false,
    ctx: null,
  });
  const timers = useRef<ReturnType<typeof setTimeout>[]>([]);

  const clearTimers = () => {
    timers.current.forEach((t) => clearTimeout(t));
    timers.current = [];
  };

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

  const approveTicket = useCallback((id: string) => {
    setTickets((prev) =>
      prev.map((t) =>
        t.id === id
          ? {
              ...t,
              status: "APPROVED",
              vendorId: "v1",
              timeline: [...t.timeline, { at: new Date().toISOString(), label: "Approved by manager" }],
            }
          : t
      )
    );
    setTimeout(() => {
      setTickets((prev) =>
        prev.map((t) =>
          t.id === id
            ? {
                ...t,
                status: "DISPATCHED",
                timeline: [
                  ...t.timeline,
                  { at: new Date().toISOString(), label: "Work order emailed", detail: "QuickFix Berlin" },
                  { at: new Date().toISOString(), label: "Status → DISPATCHED" },
                ],
              }
            : t
        )
      );
      toast.success("SMS sent to tenant", {
        description: "QuickFix Berlin arrives 2–4 PM.",
      });
    }, 2000);
  }, []);

  const rejectTicket = useCallback((id: string) => {
    setTickets((prev) =>
      prev.map((t) =>
        t.id === id
          ? {
              ...t,
              status: "REJECTED",
              timeline: [...t.timeline, { at: new Date().toISOString(), label: "Rejected by manager" }],
            }
          : t
      )
    );
    toast("Dispatch rejected", { description: "Ticket marked as REJECTED." });
  }, []);

  const updateTicket = useCallback((id: string, patch: Partial<Ticket>) => {
    setTickets((prev) =>
      prev.map((t) => {
        if (t.id !== id) return t;
        const changes = (Object.keys(patch) as (keyof Ticket)[])
          .filter((k) => t[k] !== patch[k])
          .map((k) => `${String(k)} → ${String(patch[k] ?? "—")}`);
        if (changes.length === 0) return t;
        return {
          ...t,
          ...patch,
          timeline: [
            ...t.timeline,
            { at: new Date().toISOString(), label: "Edited by manager", detail: changes.join(", ") },
          ],
        };
      })
    );
    toast("Ticket updated", { description: id });
  }, []);

  const onApprove = () => {
    const id = approval.ticketId!;
    setApproval({ open: false, ctx: null });
    closeCall();
    approveTicket(id);
  };

  const onCancel = () => {
    setApproval({ open: false, ctx: null });
    closeCall();
    toast("Decision deferred", { description: "Ticket left in PENDING_APPROVAL for review." });
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
          <button
            onClick={simulate}
            disabled={call.active}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground shadow-sm transition hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles className="h-4 w-4" />
            Simulate incoming call
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-8">
        <LiveCallPanel state={call} onSimulate={simulate} />

        <div>
          <div className="mb-3 flex items-baseline justify-between">
            <h2 className="text-sm font-semibold text-foreground">Tickets</h2>
            <p className="text-xs text-muted-foreground">{tickets.length} total · click a row for details</p>
          </div>
          <TicketsTable
            tickets={tickets}
            vendors={vendors}
            onSelect={setSelected}
            selectedId={selected?.id}
            onApproveTicket={approveTicket}
            onRejectTicket={rejectTicket}
          />
        </div>
      </main>

      <ApprovalModal open={approval.open} ctx={approval.ctx} onApprove={onApprove} onCancel={onCancel} />
      <TicketDrawer
        ticket={selected}
        vendor={selectedVendor}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}
