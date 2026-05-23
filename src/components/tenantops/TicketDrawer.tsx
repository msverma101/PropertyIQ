import { X, Phone, Bot, Mail, ArrowRightCircle, ChevronDown } from "lucide-react";
import { useState } from "react";
import type { Ticket, Vendor } from "@/lib/tenantops-data";
import { CategoryBadge, PriorityBadge, StatusBadge } from "./badges";

function iconFor(label: string) {
  const l = label.toLowerCase();
  if (l.includes("call")) return <Phone className="h-3.5 w-3.5" />;
  if (l.includes("ai")) return <Bot className="h-3.5 w-3.5" />;
  if (l.includes("email") || l.includes("work order")) return <Mail className="h-3.5 w-3.5" />;
  return <ArrowRightCircle className="h-3.5 w-3.5" />;
}

function fmt(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function TicketDrawer({
  ticket,
  vendor,
  onClose,
}: {
  ticket: Ticket | null;
  vendor?: Vendor;
  onClose: () => void;
}) {
  const [openTranscript, setOpenTranscript] = useState(false);
  if (!ticket) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="flex-1 bg-foreground/10" onClick={onClose} />
      <aside className="flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl">
        <div className="flex items-start justify-between gap-3 border-b border-border p-5">
          <div>
            <div className="font-mono text-xs text-muted-foreground">{ticket.id}</div>
            <h3 className="mt-0.5 text-base font-semibold text-foreground">
              {ticket.property} · {ticket.flat}
            </h3>
            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <CategoryBadge c={ticket.category} />
              <PriorityBadge p={ticket.priority} />
              <StatusBadge s={ticket.status} />
            </div>
          </div>
          <button
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <div className="rounded-lg border border-border bg-background/60 p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Description</div>
            <p className="mt-1.5 text-sm leading-relaxed text-foreground">{ticket.description}</p>
            {vendor && (
              <div className="mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
                Vendor · <span className="text-foreground">{vendor.name}</span> · ETA {vendor.eta}
              </div>
            )}
          </div>

          <div className="mt-6">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Timeline</div>
            <ol className="mt-3 space-y-4 border-l border-border pl-4">
              {ticket.timeline.map((e, i) => (
                <li key={i} className="relative">
                  <span className="absolute -left-[22px] top-0.5 grid h-5 w-5 place-items-center rounded-full bg-card text-muted-foreground ring-1 ring-border">
                    {iconFor(e.label)}
                  </span>
                  <div className="text-sm font-medium text-foreground">{e.label}</div>
                  {e.detail && <div className="text-xs text-muted-foreground">{e.detail}</div>}
                  <div className="text-[11px] text-muted-foreground/80">{fmt(e.at)}</div>
                </li>
              ))}
            </ol>
          </div>

          <div className="mt-6 rounded-lg border border-border">
            <button
              onClick={() => setOpenTranscript((v) => !v)}
              className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left text-sm font-medium text-foreground"
            >
              Call transcript
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${openTranscript ? "rotate-180" : ""}`} />
            </button>
            {openTranscript && (
              <div className="border-t border-border bg-background/60 p-4 text-xs leading-relaxed text-foreground/80 whitespace-pre-line">
                {ticket.transcript ?? "Transcript not available for this ticket."}
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
}