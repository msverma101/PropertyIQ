import { X, Phone, Bot, Mail, ArrowRightCircle, Clock, Building, Wrench } from "lucide-react";
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
  onDispatch,
}: {
  ticket: Ticket | null;
  vendor?: Vendor;
  onClose: () => void;
  onDispatch?: (ticket: Ticket) => void;
}) {
  if (!ticket) return null;
  const canDispatch =
    !!onDispatch &&
    ticket.status !== "DISPATCHED" &&
    ticket.status !== "RESOLVED" &&
    ticket.status !== "CLOSED";

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <div className="flex-1 bg-foreground/10" onClick={onClose} />
      <aside className="flex h-full w-full max-w-md flex-col border-l border-border bg-card shadow-xl">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-border p-5">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-primary">#{ticket.id.slice(-4)}</span>
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

          {/* Matched Vendor */}
          <div className="space-y-3">
            <div className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Matched Vendor</div>
            <div className="rounded-lg border border-border bg-background/60 p-4">
              {vendor ? (
                <div className="space-y-3">
                  <div className="flex items-center gap-2">
                    <Wrench className="h-3.5 w-3.5 text-primary" />
                    <span className="text-sm font-semibold text-foreground">{vendor.name}</span>
                  </div>
                  <div className="flex flex-col gap-1.5 text-xs text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-semibold text-primary uppercase tracking-wider w-16 shrink-0">Trade</span>
                      <span className="text-foreground">{vendor.trade}</span>
                    </div>
                    {vendor.eta && vendor.eta !== "TBD" && (
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-semibold text-primary uppercase tracking-wider w-16 shrink-0">ETA</span>
                        <Clock className="h-3 w-3 text-muted-foreground/80" />
                        <span>{vendor.eta}</span>
                      </div>
                    )}
                    {vendor.estimate > 0 && (
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-semibold text-primary uppercase tracking-wider w-16 shrink-0">Estimate</span>
                        <span className="text-foreground font-medium">€{vendor.estimate}</span>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="text-xs text-muted-foreground">No vendor matched yet.</div>
              )}
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

        </div>

        {/* Footer */}
        {canDispatch && (
          <div className="border-t border-border bg-muted/30 px-5 py-3 flex items-center justify-between gap-3">
            <span className="text-[10px] text-muted-foreground">
              Auto-picks the top vendor for {ticket.category}.
            </span>
            <button
              onClick={() => onDispatch?.(ticket)}
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition hover:opacity-95"
            >
              Dispatch Vendor
            </button>
          </div>
        )}
        {ticket.updatedAt && (
          <div className="border-t border-border bg-muted/30 px-5 py-3 text-right text-[10px] text-muted-foreground">
            Last Updated: {fmt(ticket.updatedAt)}
          </div>
        )}
      </aside>
    </div>
  );
}