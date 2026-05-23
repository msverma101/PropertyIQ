import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { Ticket, Vendor, Priority, Category } from "@/lib/tenantops-data";
import { CategoryBadge, PriorityBadge, StatusBadge } from "./badges";

const priorities: (Priority | "ALL")[] = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"];
const categories: (Category | "ALL")[] = ["ALL", "Plumbing", "Electrical", "Heating", "Locksmith", "Appliance"];

function fmtDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" }) +
    " · " + d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
}

export function TicketsTable({
  tickets,
  vendors,
  onSelect,
  selectedId,
}: {
  tickets: Ticket[];
  vendors: Vendor[];
  onSelect: (t: Ticket) => void;
  selectedId?: string;
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
                      <CategoryBadge c={t.category} />
                    </div>
                    <div className="mt-1 line-clamp-1 max-w-[360px] text-xs text-muted-foreground">{t.description}</div>
                  </Td>
                  <Td><PriorityBadge p={t.priority} /></Td>
                  <Td><StatusBadge s={t.status} /></Td>
                  <Td className="text-foreground/80">{v?.name ?? <span className="text-muted-foreground">—</span>}</Td>
                  <Td className="text-xs text-muted-foreground">{fmtDate(t.createdAt)}</Td>
                </tr>
              );
            })}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-10 text-center text-sm text-muted-foreground">
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