import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";

const ELEVENLABS_AGENT_ID =
  (import.meta.env.VITE_ELEVENLABS_AGENT_ID as string | undefined) ?? "";
const ELEVENLABS_WIDGET_SCRIPT = "https://unpkg.com/@elevenlabs/convai-widget-embed";

export const Route = createFileRoute("/call")({
  component: CallPage,
});

const EXAMPLE_ISSUES = [
  "Leaky radiator",
  "Broken door lock",
  "No hot water",
  "Heating not working",
  "Water damage",
  "Electrical fault",
];

function CallPage() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    if (document.querySelector(`script[src="${ELEVENLABS_WIDGET_SCRIPT}"]`)) return;
    const script = document.createElement("script");
    script.src = ELEVENLABS_WIDGET_SCRIPT;
    script.async = true;
    script.type = "text/javascript";
    document.body.appendChild(script);
  }, []);

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{
        background: "linear-gradient(135deg, #0f172a 0%, #1e1b4b 40%, #0f172a 100%)",
      }}
    >
      {/* Subtle grid pattern overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.04) 1px, transparent 0)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Main content — centered vertically */}
      <div className="relative flex-1 flex flex-col items-center justify-center px-6 py-16">

        {/* Brand mark */}
        <div className="flex flex-col items-center gap-4 mb-12">
          {/* Avatar circle */}
          <div
            className="relative w-28 h-28 rounded-full flex items-center justify-center shadow-2xl"
            style={{
              background: "linear-gradient(135deg, #4f46e5, #7c3aed)",
              boxShadow: "0 0 0 6px rgba(99,102,241,0.15), 0 0 0 12px rgba(99,102,241,0.08), 0 20px 60px rgba(99,102,241,0.4)",
            }}
          >
            <img
              src="/helloTheo-avatar.svg"
              alt="HelloTheo avatar"
              className="w-16 h-16"
            />
            {/* Online pulse dot */}
            <span
              className="absolute bottom-1 right-1 w-5 h-5 rounded-full border-2 border-[#0f172a]"
              style={{ background: "#22c55e" }}
            >
              <span
                className="absolute inset-0 rounded-full animate-ping"
                style={{ background: "#22c55e", opacity: 0.6 }}
              />
            </span>
          </div>

          {/* Brand name */}
          <div className="text-center">
            <h1
              className="text-4xl font-bold tracking-tight"
              style={{ color: "#f8fafc" }}
            >
              HelloTheo
            </h1>
            <p className="text-sm font-medium mt-1" style={{ color: "#6366f1" }}>
              Property Maintenance Hotline
            </p>
          </div>
        </div>

        {/* Main CTA section */}
        <div className="text-center max-w-lg mb-10">
          <h2
            className="text-2xl font-semibold mb-3 leading-snug"
            style={{ color: "#e2e8f0" }}
          >
            Report a maintenance issue in seconds
          </h2>
          <p className="text-base leading-relaxed" style={{ color: "#94a3b8" }}>
            Theo is standing by 24/7. Tap the button in the
            <strong style={{ color: "#c7d2fe" }}> bottom-right corner</strong> to
            start a voice call — no hold music, no forms.
          </p>
        </div>

        {/* Example issues */}
        <div className="flex flex-wrap justify-center gap-2 mb-12 max-w-md">
          {EXAMPLE_ISSUES.map((issue) => (
            <span
              key={issue}
              className="px-3 py-1.5 rounded-full text-sm font-medium"
              style={{
                background: "rgba(99,102,241,0.12)",
                color: "#a5b4fc",
                border: "1px solid rgba(99,102,241,0.25)",
              }}
            >
              {issue}
            </span>
          ))}
        </div>

        {/* How it works — 3 steps */}
        <div
          className="w-full max-w-lg rounded-2xl p-6 mb-12"
          style={{
            background: "rgba(255,255,255,0.04)",
            border: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "#6366f1" }}>
            How it works
          </p>
          <div className="space-y-4">
            {[
              { n: "1", title: "Tap the button", desc: "Hit the purple call button in the bottom-right corner." },
              { n: "2", title: "Describe the issue", desc: "Speak naturally — Theo will ask clarifying questions." },
              { n: "3", title: "Done", desc: "Your request is logged and a tradesperson is dispatched." },
            ].map(({ n, title, desc }) => (
              <div key={n} className="flex items-start gap-3">
                <div
                  className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
                  style={{ background: "rgba(99,102,241,0.2)", color: "#818cf8" }}
                >
                  {n}
                </div>
                <div>
                  <p className="text-sm font-semibold" style={{ color: "#e2e8f0" }}>{title}</p>
                  <p className="text-sm" style={{ color: "#64748b" }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Animated arrow pointing to the widget */}
        <div className="fixed bottom-32 right-6 pointer-events-none z-10 flex flex-col items-end gap-1">
          <p
            className="text-sm font-semibold"
            style={{ color: "#a5b4fc", textShadow: "0 1px 4px rgba(0,0,0,0.8)" }}
          >
            Tap here to call
          </p>
          {/* Arrow using pure CSS/SVG pointing down-right */}
          <svg
            width="40"
            height="40"
            viewBox="0 0 40 40"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            style={{ filter: "drop-shadow(0 1px 4px rgba(0,0,0,0.8))" }}
            className="animate-bounce"
          >
            <path
              d="M8 8 L32 32 M18 32 L32 32 L32 18"
              stroke="#818cf8"
              strokeWidth="3"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        {/* Trust signals footer */}
        <div className="flex items-center gap-6 flex-wrap justify-center">
          {[
            { icon: "🔒", label: "Private & secure" },
            { icon: "⚡", label: "Average 4-min response" },
            { icon: "🗓", label: "Available 24/7" },
          ].map(({ icon, label }) => (
            <div key={label} className="flex items-center gap-1.5">
              <span className="text-base">{icon}</span>
              <span className="text-xs font-medium" style={{ color: "#475569" }}>
                {label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ElevenLabs widget — mounted client-side only */}
      {mounted && (
        // @ts-expect-error custom element from @elevenlabs/convai-widget-embed
        <elevenlabs-convai
          agent-id={ELEVENLABS_AGENT_ID}
          action-text="Call HelloTheo"
          avatar-image-url="/helloTheo-avatar.svg"
        />
      )}
    </div>
  );
}
