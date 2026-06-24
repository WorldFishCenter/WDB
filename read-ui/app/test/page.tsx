"use client";

import { useState, useMemo } from "react";
import { AnswerView } from "@/components/AnswerView";
import { SourceViewerProvider } from "@/components/source/SourceViewerProvider";
import type { RouterAnswer } from "@/lib/contract";
import fixtureData from "@/fixtures/blended_abc.json";

/**
 * Test page: renders the blended_abc fixture directly to verify layout without the API.
 * Visit /test to see the full vertical-flow layout with real data.
 */
export default function TestPage() {
  const answer = fixtureData as RouterAnswer;

  // Stub global node map
  const globalNodeMap = useMemo(() => {
    return new Map<string, { label: string; community: number; file_type?: string; source_file?: string }>();
  }, []);

  return (
    <SourceViewerProvider>
      <div style={{ background: "var(--wf-bg)", minHeight: "100vh" }}>
        <div className="wf-container" style={{ padding: "8px 24px 80px" }}>
          <AnswerView answer={answer} globalNodeMap={globalNodeMap} />
        </div>
      </div>
    </SourceViewerProvider>
  );
}
