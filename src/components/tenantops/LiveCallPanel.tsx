import { PhoneCall, PhoneOff, Sparkles } from "lucide-react";
import { Avatar, CategoryBadge, PriorityBadge } from "./badges";
import type { Tenant, Category, Priority } from "@/lib/tenantops-data";

export interface LiveCallState {
  active: boolean;
  tenant?: Tenant;
  description?: string;
  category?: Category;
  priority?: Priority;
  confidence?: number;
  step: number; // 0..5
}

export function LiveCallPanel({ state, onSimulate }: { state: LiveCallState; onSimulate: () => void }) {
  if (!state.active) {
    return (
      <section className="rounded-xl border border-border bg-card p-6">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-full bg-muted text-muted-foreground">
              <PhoneOff className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-medium text-foreground">No active call</div>
              <p className="text-xs text-muted-foreground">The AI voice agent is on standby.</p>
            </div>
          </div>
          <button
            onClick={onSimulate}
            className="inline-flex items-center gap-2 rounded-md bg-primary px-3.5 py-2 text-sm font-medium text-primary-foreground shadow-sm transition hover:opacity-95"
          >
            <Sparkles className="h-4 w-4" />
            Simulate incoming call
          </button>
        </div>
      </section>
    );
  }

  const { tenant, description, category, priority, confidence = 0, step } = state;

  return (
    <section className="rounded-xl border border-border bg-card p-6">
      <div className="flex items-start justify-between gap-6">
        <div className="flex items-start gap-4">
          <Avatar initials={tenant?.initials ?? "—"} />
          <div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-md bg-[color:var(--status-active-bg)] px-2 py-0.5 text-[11px] font-medium text-[color:var(--status-active)]">
                <span className="h-1.5 w-1.5 rounded-full bg-[color:var(--status-active)]" />
                Call active
              </span>
              <span className="rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                Tenant
              </span>
            </div>
            <div className="mt-1 text-base font-semibold text-foreground">{tenant?.name}</div>
            <div className="text-xs text-muted-foreground">
              {tenant?.property} · {tenant?.flat}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <PhoneCall className="h-3.5 w-3.5" />
          AI agent · listening
        </div>
      </div>

      <div className="mt-6 grid gap-3 rounded-lg border border-border bg-background/60 p-4">
        <Field label="Defect description">
          {step >= 1 ? (
            <p key={description} className="animate-settle text-sm leading-relaxed text-foreground">
              {description}
              {step === 1 && <span className="ml-0.5 inline-block h-3 w-1.5 translate-y-0.5 bg-foreground/60 align-baseline" />}
            </p>
          ) : (
            <Skeleton />
          )}
        </Field>
        <Field label="Category">
          {step >= 2 && category ? (
            <div className="animate-settle">
              <CategoryBadge c={category} />
            </div>
          ) : (
            <Skeleton w="w-24" />
          )}
        </Field>
        <Field label="Priority">
          {step >= 3 && priority ? (
            <div className="animate-settle">
              <PriorityBadge p={priority} />
            </div>
          ) : (
            <Skeleton w="w-16" />
          )}
        </Field>
        <Field label="AI confidence">
          {step >= 4 ? (
            <div className="animate-settle flex items-center gap-3">
              <div className="h-1.5 w-48 overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-[color:var(--status-active)] transition-all duration-700"
                  style={{ width: `${confidence}%` }}
                />
              </div>
              <span className="font-mono text-xs text-muted-foreground">{confidence}%</span>
            </div>
          ) : (
            <Skeleton w="w-48" />
          )}
        </Field>
      </div>
    </section>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-[140px_1fr] items-start gap-4">
      <div className="pt-0.5 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</div>
      <div className="min-h-[20px]">{children}</div>
    </div>
  );
}

function Skeleton({ w = "w-3/4" }: { w?: string }) {
  return <div className={`h-3 ${w} rounded bg-muted/70`} />;
}