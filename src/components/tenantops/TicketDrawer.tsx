import { X, Phone, Bot, Mail, ArrowRightCircle, ChevronDown, Clock, Building } from "lucide-react";
import { useState } from "react";
import type { Ticket, Vendor } from "@/lib/tenantops-data";
import { CategoryBadge, PriorityBadge, StatusBadge } from "./badges";

function iconFor(label: string) {
  const l = label.toLowerCase();
  if (l.includes("call")) return <Phone className="h-3.5 w-3.5" />;
  if (l.includes("ai") || l.includes("tool") || l.includes("invoked") || l.includes("read_context") || l.includes("update") || l.includes("search")) return <Bot className="h-3.5 w-3.5" />;
  if (l.includes("email") || l.includes("work order")) return <Mail className="h-3.5 w-3.5" />;
  return <ArrowRightCircle className="h-3.5 w-3.5" />;
}

function fmt(iso: string) {
  if (!iso) return "—";
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
  const [openTranscript, setOpenTranscript] = useState(true);
  if (!ticket) return null;

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="flex-1 bg-foreground/10" onClick={onClose} />
      <aside className="flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-border p-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-primary">{ticket.id}</span>
              <span className="text-[10px] text-muted-foreground">·</span>
              <span className="text-[10px] text-muted-foreground flex items-center gap-1">
                <Clock className="h-2.5 w-2.5" />
                {fmt(ticket.createdAt)}
              </span>
            </div>
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

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-6">
          {/* Description */}
          <div className="rounded-lg border border-border bg-background/60 p-4">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Description</div>
            <p className="mt-1.5 text-sm leading-relaxed text-foreground">{ticket.description}</p>
            {vendor && (
              <div className="mt-3 border-t border-border pt-3 text-xs text-muted-foreground">
                Vendor · <span className="text-foreground">{vendor.name}</span> · ETA {vendor.eta}
              </div>
            )}
          </div>

          {/* Property & Contacts */}
          <div className="space-y-3">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Property & Contacts</div>
            <div className="rounded-lg border border-border bg-background/60 p-4 space-y-4">
              {/* Tenant details */}
              <div>
                <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">Tenant</span>
                <div className="mt-1 text-sm font-semibold text-foreground">
                  {ticket.tenantDetails?.name || "Lisa Müller"}
                </div>
                <div className="mt-1.5 flex flex-col gap-1.5 text-xs text-muted-foreground">
                  <div className="flex items-center gap-2">
                    <Phone className="h-3 w-3 text-muted-foreground/80" />
                    <span>{ticket.tenantDetails?.phone || "+49 170 1234567"}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Mail className="h-3 w-3 text-muted-foreground/80" />
                    <span className="truncate">{ticket.tenantDetails?.email || "lisa.mueller@example.com"}</span>
                  </div>
                </div>
              </div>

              {/* Property details */}
              <div className="border-t border-border pt-3">
                <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">Property Address</span>
                <div className="mt-1 text-xs font-medium text-foreground flex items-center gap-1.5">
                  <Building className="h-3 w-3 text-muted-foreground" />
                  <span>{ticket.propertyDetails?.address || ticket.property}</span>
                </div>
                <div className="mt-0.5 ml-4.5 text-xs text-muted-foreground">
                  Zipcode: {ticket.propertyDetails?.zipcode || "10115"}
                </div>
              </div>

              {/* Owner details */}
              <div className="border-t border-border pt-3">
                <span className="text-[10px] font-semibold text-primary uppercase tracking-wider">Owners</span>
                <div className="mt-2 space-y-3">
                  {ticket.owners && ticket.owners.length > 0 ? (
                    ticket.owners.map((owner) => (
                      <div key={owner.id} className="text-xs">
                        <div className="font-semibold text-foreground">{owner.name}</div>
                        <div className="mt-1 flex flex-col gap-1 text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <Phone className="h-3 w-3 text-muted-foreground/80" />
                            <span>{owner.phone}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Mail className="h-3 w-3 text-muted-foreground/80" />
                            <span className="truncate">{owner.email}</span>
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-muted-foreground">No registered owners found.</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Timeline */}
          <div>
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground font-semibold">Timeline & Background Actions</div>
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

          {/* Call Transcript */}
          <div className="rounded-lg border border-border overflow-hidden">
            <button
              onClick={() => setOpenTranscript((v) => !v)}
              className="flex w-full items-center justify-between gap-2 bg-background/40 px-4 py-3 text-left text-sm font-semibold text-foreground"
            >
              <span>Call Transcript</span>
              <ChevronDown className={`h-4 w-4 text-muted-foreground transition-transform ${openTranscript ? "rotate-180" : ""}`} />
            </button>
            {openTranscript && (
              <div className="border-t border-border bg-background/65 p-4 font-mono text-[11px] leading-relaxed text-foreground/85 whitespace-pre-line max-h-60 overflow-y-auto">
                {ticket.transcript ?? "Transcript not available for this ticket."}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        {ticket.updatedAt && (
          <div className="border-t border-border bg-muted/30 px-5 py-3 text-right text-[10px] text-muted-foreground">
            Last Updated: {fmt(ticket.updatedAt)}
          </div>
        )}
      </aside>
    </div>
  );
}