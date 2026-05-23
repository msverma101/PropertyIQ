import type { Priority, Status, Category } from "@/lib/tenantops-data";

const priorityStyles: Record<Priority, string> = {
  CRITICAL: "bg-[color:var(--status-critical-bg)] text-[color:var(--status-critical)] ring-[color:var(--status-critical)]/20",
  HIGH: "bg-[color:var(--status-pending-bg)] text-[color:var(--status-pending)] ring-[color:var(--status-pending)]/20",
  MEDIUM: "bg-[color:var(--status-info-bg)] text-[color:var(--status-info)] ring-[color:var(--status-info)]/20",
  LOW: "bg-[color:var(--status-neutral-bg)] text-[color:var(--status-neutral)] ring-[color:var(--status-neutral)]/20",
};

export function PriorityBadge({ p }: { p: Priority }) {
  return (
    <span
      className={`inline-flex items-center rounded-md px-1.5 py-0.5 text-[10px] font-semibold tracking-wider ring-1 ring-inset ${priorityStyles[p]}`}
    >
      {p}
    </span>
  );
}

const statusStyles: Record<Status, string> = {
  NEW: "bg-[color:var(--status-info-bg)] text-[color:var(--status-info)]",
  PENDING_APPROVAL: "bg-[color:var(--status-pending-bg)] text-[color:var(--status-pending)]",
  APPROVED: "bg-[color:var(--status-active-bg)] text-[color:var(--status-active)]",
  DISPATCHED: "bg-[color:var(--status-active-bg)] text-[color:var(--status-active)]",
  RESOLVED: "bg-[color:var(--status-active-bg)] text-[color:var(--status-active)]",
  CLOSED: "bg-[color:var(--status-neutral-bg)] text-[color:var(--status-neutral)]",
  REJECTED: "bg-[color:var(--status-critical-bg)] text-[color:var(--status-critical)]",
};

export function StatusBadge({ s }: { s: Status }) {
  return (
    <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-[11px] font-medium ${statusStyles[s]}`}>
      {s.replace("_", " ")}
    </span>
  );
}

export function CategoryBadge({ c }: { c: Category }) {
  return (
    <span className="inline-flex items-center rounded-md bg-[color:var(--status-neutral-bg)] px-2 py-0.5 text-[11px] font-medium text-foreground/70 ring-1 ring-inset ring-border">
      {c}
    </span>
  );
}

export function Avatar({ initials }: { initials: string }) {
  return (
    <div className="grid h-9 w-9 place-items-center rounded-full bg-[color:var(--accent)] text-[12px] font-semibold text-[color:var(--accent-foreground)] ring-1 ring-inset ring-border">
      {initials}
    </div>
  );
}