"use client";

/**
 * DEV-ONLY fixtures preview — renders the captured /answer fixtures through the real AnswerView,
 * with no backend running. Each fixture is one honesty state (single A, computed C, full blend,
 * partial blend, refusal, verified negative, disambiguation), so the redesign can be verified
 * offline against the EXACT API shapes.
 * Not linked from the app; reachable at /preview.
 */

import { useEffect, useState } from "react";
import { SourceViewerProvider } from "@/components/source/SourceViewerProvider";
import { AnswerView } from "@/components/AnswerView";
import type { RouterAnswer } from "@/lib/contract";

import single_mode_a from "@/fixtures/single_mode_a.json";
import quantitative_c from "@/fixtures/quantitative_c.json";
import blended_abc from "@/fixtures/blended_abc.json";
import partial_blend from "@/fixtures/partial_blend.json";
import refusal from "@/fixtures/refusal.json";
import verified_negative from "@/fixtures/verified_negative.json";
import disambiguation_c from "@/fixtures/disambiguation_c.json";

const FIXTURES: { key: string; label: string; data: RouterAnswer }[] = [
  { key: "single_mode_a", label: "Single · Mode A", data: single_mode_a as RouterAnswer },
  { key: "quantitative_c", label: "Computed · Mode C", data: quantitative_c as RouterAnswer },
  { key: "blended_abc", label: "Full blend · A+B+C", data: blended_abc as RouterAnswer },
  { key: "partial_blend", label: "Partial blend", data: partial_blend as RouterAnswer },
  { key: "refusal", label: "Honest refusal", data: refusal as RouterAnswer },
  // the two states that had no fixture at all — and the two the router used to flatten
  {
    key: "verified_negative",
    label: "Verified negative · Mode A",
    data: verified_negative as RouterAnswer,
  },
  {
    key: "disambiguation_c",
    label: "Needs disambiguation · Mode C",
    data: disambiguation_c as RouterAnswer,
  },
];

export default function PreviewPage() {
  const [active, setActive] = useState(0);
  // Read ?f=<key> after mount (avoids SSR/client hydration mismatch).
  useEffect(() => {
    const key = new URLSearchParams(window.location.search).get("f");
    const i = FIXTURES.findIndex((f) => f.key === key);
    if (i >= 0) setActive(i);
  }, []);
  const fixture = FIXTURES[active];

  return (
    <SourceViewerProvider>
      <div
        style={{
          position: "sticky",
          top: 0,
          zIndex: 50,
          display: "flex",
          alignItems: "center",
          gap: "var(--wf-space-2)",
          flexWrap: "wrap",
          padding: "var(--wf-space-3) var(--wf-space-6)",
          background: "var(--wf-surface-header)",
          backdropFilter: "var(--wf-surface-header-blur)",
          borderBottom: "1px solid var(--wf-border-header)",
        }}
      >
        <span
          style={{
            fontSize: "var(--wf-text-micro)",
            fontWeight: 700,
            textTransform: "uppercase",
            letterSpacing: "0.08em",
            color: "var(--wf-text-muted)",
            marginRight: "var(--wf-space-2)",
          }}
        >
          Fixtures preview
        </span>
        {FIXTURES.map((f, i) => (
          <button
            key={f.key}
            onClick={() => setActive(i)}
            style={{
              padding: "var(--wf-space-1) var(--wf-space-3)",
              borderRadius: "var(--wf-radius-pill)",
              fontSize: "var(--wf-text-caption)",
              fontWeight: 600,
              border: "1px solid",
              borderColor: i === active ? "var(--wf-border-accent-medium)" : "var(--wf-border)",
              background: i === active ? "var(--wf-mode-a-bg)" : "var(--wf-surface-inset)",
              color: i === active ? "var(--wf-accent)" : "var(--wf-text-3)",
            }}
          >
            {f.label}
          </button>
        ))}
      </div>

      <main className="wf-container" style={{ paddingBottom: "var(--wf-space-11)" }}>
        <AnswerView answer={fixture.data} />
      </main>
    </SourceViewerProvider>
  );
}
