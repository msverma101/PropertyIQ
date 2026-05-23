export type Priority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type Status =
  | "NEW"
  | "PENDING_APPROVAL"
  | "APPROVED"
  | "DISPATCHED"
  | "RESOLVED"
  | "CLOSED"
  | "REJECTED";
export type Category = "Plumbing" | "Electrical" | "Heating" | "Locksmith" | "Appliance";

export interface Tenant {
  id: string;
  name: string;
  initials: string;
  property: string;
  flat: string;
}

export interface Vendor {
  id: string;
  name: string;
  trade: Category;
  eta: string;
  estimate: number;
}

export interface TimelineEvent {
  at: string;
  label: string;
  detail?: string;
}

export interface Ticket {
  id: string;
  tenantId: string;
  property: string;
  flat: string;
  category: Category;
  description: string;
  priority: Priority;
  status: Status;
  vendorId?: string;
  createdAt: string;
  timeline: TimelineEvent[];
  transcript?: string;
}

export const tenants: Tenant[] = [
  { id: "t1", name: "Lisa Chen", initials: "LC", property: "Kastanienallee 12", flat: "Flat 3B" },
  { id: "t2", name: "Marco Bauer", initials: "MB", property: "Rosenthaler Str. 48", flat: "Flat 7A" },
  { id: "t3", name: "Amira Haddad", initials: "AH", property: "Sonnenallee 102", flat: "Flat 2C" },
  { id: "t4", name: "Jonas Weber", initials: "JW", property: "Bergmannstr. 21", flat: "Flat 1A" },
  { id: "t5", name: "Priya Shah", initials: "PS", property: "Kastanienallee 12", flat: "Flat 5D" },
];

export const vendors: Vendor[] = [
  { id: "v1", name: "QuickFix Berlin", trade: "Plumbing", eta: "2–4 PM today", estimate: 180 },
  { id: "v2", name: "Volt & Watt GmbH", trade: "Electrical", eta: "Tomorrow morning", estimate: 240 },
  { id: "v3", name: "Warmhaus Heating", trade: "Heating", eta: "Within 24h", estimate: 320 },
  { id: "v4", name: "Schlüssel24", trade: "Locksmith", eta: "Within 1h", estimate: 140 },
];

const now = Date.now();
const ago = (h: number) => new Date(now - h * 3600_000).toISOString();

export const seedTickets: Ticket[] = [
  {
    id: "TKT-2041",
    tenantId: "t2",
    property: "Rosenthaler Str. 48",
    flat: "Flat 7A",
    category: "Heating",
    description: "Radiator in living room cold, no heat since morning.",
    priority: "HIGH",
    status: "DISPATCHED",
    vendorId: "v3",
    createdAt: ago(6),
    timeline: [
      { at: ago(6), label: "Call received", detail: "Tenant called the AI line." },
      { at: ago(5.9), label: "AI categorized", detail: "Heating · HIGH (94% confidence)" },
      { at: ago(5.7), label: "Approved by manager" },
      { at: ago(5.6), label: "Work order emailed", detail: "Warmhaus Heating" },
      { at: ago(5.5), label: "Status → DISPATCHED" },
    ],
    transcript:
      "Tenant: Hi, my radiator hasn't come on all morning, it's freezing.\nAI: I'm sorry to hear that. Can you confirm the flat number?\nTenant: 7A, Rosenthaler 48...",
  },
  {
    id: "TKT-2040",
    tenantId: "t3",
    property: "Sonnenallee 102",
    flat: "Flat 2C",
    category: "Electrical",
    description: "Kitchen circuit keeps tripping when the kettle is used.",
    priority: "MEDIUM",
    status: "APPROVED",
    vendorId: "v2",
    createdAt: ago(11),
    timeline: [
      { at: ago(11), label: "Call received" },
      { at: ago(10.9), label: "AI categorized", detail: "Electrical · MEDIUM" },
      { at: ago(10.5), label: "Approved by manager" },
    ],
    transcript: "Tenant: Every time we boil water the kitchen fuse goes...",
  },
  {
    id: "TKT-2039",
    tenantId: "t4",
    property: "Bergmannstr. 21",
    flat: "Flat 1A",
    category: "Locksmith",
    description: "Locked out of flat, key broke inside the lock.",
    priority: "CRITICAL",
    status: "RESOLVED",
    vendorId: "v4",
    createdAt: ago(26),
    timeline: [
      { at: ago(26), label: "Call received" },
      { at: ago(25.95), label: "AI categorized", detail: "Locksmith · CRITICAL" },
      { at: ago(25.9), label: "Auto-dispatched (after-hours rule)" },
      { at: ago(25), label: "Resolved on-site" },
    ],
    transcript: "Tenant: I'm stuck outside my door, the key snapped...",
  },
  {
    id: "TKT-2038",
    tenantId: "t5",
    property: "Kastanienallee 12",
    flat: "Flat 5D",
    category: "Plumbing",
    description: "Slow drain in bathroom sink, not urgent.",
    priority: "LOW",
    status: "NEW",
    createdAt: ago(2),
    timeline: [
      { at: ago(2), label: "Call received" },
      { at: ago(1.95), label: "AI categorized", detail: "Plumbing · LOW (88%)" },
    ],
  },
  {
    id: "TKT-2037",
    tenantId: "t2",
    property: "Rosenthaler Str. 48",
    flat: "Flat 7A",
    category: "Appliance",
    description: "Dishwasher won't start, no error code displayed.",
    priority: "MEDIUM",
    status: "CLOSED",
    createdAt: ago(72),
    timeline: [
      { at: ago(72), label: "Call received" },
      { at: ago(70), label: "Resolved — reset solved it" },
      { at: ago(69), label: "Closed" },
    ],
  },
  {
    id: "TKT-2036",
    tenantId: "t3",
    property: "Sonnenallee 102",
    flat: "Flat 2C",
    category: "Heating",
    description: "Boiler making loud knocking sound at night.",
    priority: "MEDIUM",
    status: "REJECTED",
    createdAt: ago(40),
    timeline: [
      { at: ago(40), label: "Call received" },
      { at: ago(39.9), label: "AI categorized", detail: "Heating · MEDIUM" },
      { at: ago(39), label: "Rejected — duplicate of TKT-2030" },
    ],
  },
  {
    id: "TKT-2035",
    tenantId: "t4",
    property: "Bergmannstr. 21",
    flat: "Flat 1A",
    category: "Electrical",
    description: "Hallway light flickers intermittently.",
    priority: "LOW",
    status: "NEW",
    createdAt: ago(4),
    timeline: [
      { at: ago(4), label: "Call received" },
      { at: ago(3.95), label: "AI categorized", detail: "Electrical · LOW" },
    ],
  },
];