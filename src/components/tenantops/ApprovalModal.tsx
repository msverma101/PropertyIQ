import { ShieldCheck, X } from "lucide-react";

export interface ApprovalContext {
  tenantName: string;
  category: string;
  summary: string;
  vendorName: string;
  estimate: number;
}

export function ApprovalModal({
  open,
  ctx,
  onApprove,
  onCancel,
}: {
  open: boolean;
  ctx: ApprovalContext | null;
  onApprove: () => void;
  onCancel: () => void;
}) {
  if (!open || !ctx) return null;

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-foreground/20 p-4 backdrop-blur-[2px]">
      <div className="w-full max-w-lg rounded-xl border border-border bg-card shadow-xl">
        <div className="flex items-start justify-between gap-4 border-b border-border p-5">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-md bg-[color:var(--status-pending-bg)] text-[color:var(--status-pending)]">
              <ShieldCheck className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-foreground">Authorization required</h2>
              <p className="text-xs text-muted-foreground">Vendor dispatch needs a manager approval.</p>
            </div>
          </div>
          <button
            onClick={onCancel}
            className="rounded-md p-1 text-muted-foreground transition hover:bg-muted hover:text-foreground"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4 p-5">
          <p className="text-sm leading-relaxed text-foreground">
            Tenant <span className="font-medium">{ctx.tenantName}</span> reports an active{" "}
            <span className="font-medium">{ctx.summary}</span>. {ctx.category === "Plumbing" ? "Plumber" : "Vendor"}{" "}
            <span className="font-medium">{ctx.vendorName}</span> available for dispatch. Est.{" "}
            <span className="font-mono">€{ctx.estimate}</span>.
          </p>

          <div className="rounded-lg border border-border bg-background/60 p-3 text-xs text-muted-foreground">
            Cancel keeps the ticket in <span className="font-medium">PENDING_APPROVAL</span> so you can decide from the ticket list. Approve dispatches the vendor immediately.
          </div>
        </div>

        <div className="flex items-center justify-end gap-2 border-t border-border p-4">
          <button
            onClick={onCancel}
            className="rounded-md border border-border bg-background px-3.5 py-2 text-sm font-medium text-foreground transition hover:bg-muted"
          >
            Cancel
          </button>
          <button
            onClick={onApprove}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm transition hover:opacity-95"
          >
            Approve &amp; Dispatch
          </button>
        </div>
      </div>
    </div>
  );
}