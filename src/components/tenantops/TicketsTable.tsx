import { Search, Check, X } from "lucide-react";
import { useMemo, useState } from "react";
import type { Ticket, Vendor, Priority, Category, Status } from "@/lib/tenantops-data";
import { CategoryBadge, PriorityBadge, StatusBadge } from "./badges";

const priorities: (Priority | "ALL")[] = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"];
const categories: (Category | "ALL")[] = ["ALL", "Plumbing", "Electrical", "Heating", "Locksmith", "Appliance"];
const editablePriorities: Priority[] = ["CRITICAL", "HIGH", "MEDIUM", "LOW"];
const editableCategories: Category[] = ["Plumbing", "Electrical", "Heating", "Locksmith", "Appliance"];
const editableStatuses: Status[] = ["NEW", "PENDING_APPROVAL", "APPROVED", "DISPATCHED", "RESOLVED", "CLOSED", "REJECTED"];

function fmtDate(iso: string) {
  const d = new Date(iso);
  const day = String(d.getUTCDate()).padStart(2, "0");
  const month = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][d.getUTCMonth()];
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${day} ${month} · ${hh}:${mm}`;
}

export function TicketsTable({
  tickets,
  vendors,
  onSelect,
  selectedId,
  onApproveTicket,
  onRejectTicket,
  onUpdateTicket,
}: {
  tickets: Ticket[];
  vendors: Vendor[];
  onSelect: (t: Ticket) => void;
  selectedId?: string;
  onApproveTicket: (id: string) => void;
  onRejectTicket: (id: string) => void;
  onUpdateTicket: (id: string, patch: Partial<Ticket>) => void;
}) {
  const [q, setQ] = useState("");
  const [prio, setPrio] = useState<Priority | "ALL">("ALL");
  const [cat, setCat] = useState<Category | "ALL">("ALL");

  const filtered = useMemo(() => {
    return tickets.filter((t) => {
      if (prio !== "ALL" && t.priority !== prio) return false;
      if (cat !== "ALL" && t.category !== cat) return false;
      if (q) {
        const s = q.toLowerCase();
        if (
          !t.id.toLowerCase().includes(s) &&
          !t.description.toLowerCase().includes(s) &&
          !t.property.toLowerCase().includes(s)
        )
          return false;
      }
      return true;
    });
  }, [tickets, q, prio, cat]);

  return (
    <section className="rounded-xl border border-border bg-card">
      <div className="flex flex-wrap items-center gap-3 border-b border-border p-4">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search tickets, properties, descriptions…"
            className="w-full rounded-md border border-border bg-background py-2 pl-9 pr-3 text-sm placeholder:text-muted-foreground/70 focus:outline-none focus:ring-2 focus:ring-ring/40"
          />
        </div>
        <Select label="Priority" value={prio} onChange={(v) => setPrio(v as Priority | "ALL")} options={priorities} />
        <Select label="Category" value={cat} onChange={(v) => setCat(v as Category | "ALL")} options={categories} />
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
              <Th>Ticket</Th>
              <Th>Property</Th>
              <Th>Issue</Th>
              <Th>Priority</Th>
              <Th>Status</Th>
              <Th>Vendor</Th>
              <Th>Created</Th>
              <Th>Actions</Th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t) => {
              const v = vendors.find((vv) => vv.id === t.vendorId);
              const selected = selectedId === t.id;
              return (
                <tr
                  key={t.id}
                  onClick={() => onSelect(t)}
                  className={`cursor-pointer border-t border-border transition-colors hover:bg-muted/50 ${
                    selected ? "bg-muted/60" : ""
                  }`}
                >
                  <Td>
                    <span className="font-mono text-xs text-foreground">{t.id}</span>
                  </Td>
                  <Td>
                    <div className="font-medium text-foreground">{t.property}</div>
                    <div className="text-xs text-muted-foreground">{t.flat}</div>
                  </Td>
                  <Td>
                    <div className="flex items-center gap-2">
                      <InlineEdit
                        value={t.category}
                        options={editableCategories}
                        onChange={(v) => onUpdateTicket(t.id, { category: v as Category })}
                        render={(v) => <CategoryBadge c={v as Category} />}
                      />
                    </div>
                    <div className="mt-1 line-clamp-1 max-w-[360px] text-xs text-muted-foreground">{t.description}</div>
                  </Td>
                  <Td>
                    <InlineEdit
                      value={t.priority}
                      options={editablePriorities}
                      onChange={(val) => onUpdateTicket(t.id, { priority: val as Priority })}
                      render={(val) => <PriorityBadge p={val as Priority} />}
                    />
                  </Td>
                  <Td>
                    <InlineEdit
                      value={t.status}
                      options={editableStatuses}
                      onChange={(val) => onUpdateTicket(t.id, { status: val as Status })}
                      render={(val) => <StatusBadge s={val as Status} />}
                    />
                  </Td>
                  <Td className="text-foreground/80">
                    <InlineEdit
                      value={t.vendorId ?? ""}
                      options={["", ...vendors.map((vv) => vv.id)]}
                      labelFor={(id) => (id ? vendors.find((vv) => vv.id === id)?.name ?? id : "Unassigned")}
                      onChange={(val) => onUpdateTicket(t.id, { vendorId: val || undefined })}
                      render={(id) =>
                        id ? (
                          <span>{vendors.find((vv) => vv.id === id)?.name ?? id}</span>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )
                      }
                    />
                  </Td>
                  <Td className="text-xs text-muted-foreground">{fmtDate(t.createdAt)}</Td>
                  <Td>
                    {t.status === "PENDING_APPROVAL" ? (
                      <div className="flex items-center gap-1.5" onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => onApproveTicket(t.id)}
                          className="inline-flex items-center gap-1 rounded-md bg-primary px-2 py-1 text-xs font-medium text-primary-foreground shadow-sm transition hover:opacity-95"
                          aria-label="Approve ticket"
                        >
                          <Check className="h-3 w-3" /> Approve
                        </button>
                        <button
                          onClick={() => onRejectTicket(t.id)}
                          className="inline-flex items-center gap-1 rounded-md border border-border bg-background px-2 py-1 text-xs font-medium text-foreground transition hover:bg-muted"
                          aria-label="Reject ticket"
                        >
                          <X className="h-3 w-3" /> Reject
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-muted-foreground">—</span>
                    )}
                  </Td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-sm text-muted-foreground">
                  No tickets match your filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-4 py-3 font-medium">{children}</th>;
}
function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <td className={`px-4 py-3 align-top ${className}`}>{children}</td>;
}

function Select({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: readonly string[];
}) {
  return (
    <label className="flex items-center gap-2 text-xs text-muted-foreground">
      <span>{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-border bg-background px-2 py-1.5 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring/40"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

function InlineEdit<T extends string>({
  value,
  options,
  onChange,
  render,
  labelFor,
}: {
  value: T;
  options: readonly T[];
  onChange: (v: T) => void;
  render: (v: T) => React.ReactNode;
  labelFor?: (v: T) => string;
}) {
  return (
    <div className="relative inline-block" onClick={(e) => e.stopPropagation()}>
      <div className="pointer-events-none flex items-center gap-1">
        {render(value)}
        <span className="text-[10px] text-muted-foreground/60">▾</span>
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as T)}
        className="absolute inset-0 cursor-pointer opacity-0"
        aria-label="Edit"
      >
        {options.map((o) => (
          <option key={o} value={o}>
            {labelFor ? labelFor(o) : o}
          </option>
        ))}
      </select>
    </div>
  );
}