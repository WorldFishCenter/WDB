"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import { Header, type Health } from "@/components/Header";
import { QueryForm } from "@/components/QueryForm";
import { AnswerView } from "@/components/AnswerView";
import { ModeBadge, ConfidenceTag } from "@/components/chips";
import { SourceViewerProvider } from "@/components/source/SourceViewerProvider";
import { GlobalGraphExplorer } from "@/components/GlobalGraphExplorer";
import { askQuestion, ApiError } from "@/lib/api";
import type { RouterAnswer } from "@/lib/contract";
import styles from "./page.module.scss";

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [loading, setLoading] = useState(false);
  const [answer, setAnswer] = useState<RouterAnswer | null>(null);
  const [error, setError] = useState<{ message: string; unreachable: boolean } | null>(null);

  // States for Global Graph Explorer
  const [globalGraphOpen, setGlobalGraphOpen] = useState(false);
  const [rawGraphData, setRawGraphData] = useState<any | null>(null);

  // Fetch full graph.json from local repository on mount
  useEffect(() => {
    fetch("/api/source?path=graphify-out/graph.json")
      .then((r) => r.json())
      .then((data) => {
        if (data && !data.error && data.text) {
          try {
            const parsed = JSON.parse(data.text);
            setRawGraphData(parsed);
          } catch (err) {
            console.error("Failed to parse graph.json payload:", err);
          }
        }
      })
      .catch((err) => console.error("Error fetching graph.json:", err));
  }, []);

  // Compute a fast-lookup map of node details
  const globalNodeMap = useMemo(() => {
    const map = new Map<string, { label: string; community: number; file_type?: string }>();
    if (rawGraphData?.nodes) {
      rawGraphData.nodes.forEach((n: any) => {
        map.set(n.id, {
          label: n.label || n.id,
          community: typeof n.community === "number" ? n.community : 9,
          file_type: n.file_type,
        });
      });
    }
    return map;
  }, [rawGraphData]);

  const handleAsk = useCallback(async (question: string) => {
    setLoading(true);
    setError(null);
    setAnswer(null);
    try {
      setAnswer(await askQuestion(question));
    } catch (e) {
      const err = e as ApiError;
      setError({ message: err.message, unreachable: err.kind === "unreachable" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ ok: false, target: "unknown" }));
  }, []);

  // Deep link: /?q=… prefills and runs the question, so an answer view is shareable.
  useEffect(() => {
    const q = new URLSearchParams(window.location.search).get("q");
    if (q && q.trim()) handleAsk(q.trim());
  }, [handleAsk]);

  return (
    <SourceViewerProvider>
      <Header health={health} onExploreGraph={() => setGlobalGraphOpen(true)} />

      <section className={styles.hero}>
        <div className="wf-container">
          <h1 className={styles.title}>Ask the knowledge base</h1>
          <p className={styles.tagline}>
            Every claim cites its source. What can&apos;t be grounded is stated, never invented.
          </p>
          <QueryForm onSubmit={handleAsk} loading={loading} />
        </div>
      </section>

      <main className={`wf-container ${styles.main}`}>
        {loading && <LoadingState />}

        {error && (
          <div className={`${styles.error} ${error.unreachable ? styles.errorUnreachable : ""}`}>
            <strong className={styles.errorTitle}>
              {error.unreachable ? "Can’t reach the local API" : "Something went wrong"}
            </strong>
            <p>{error.message}</p>
            {error.unreachable && (
              <p className={styles.errorHint}>
                Start it from the repo root: <code>uv run uvicorn wdb_api.app:app</code>
              </p>
            )}
          </div>
        )}

        {!loading && !error && answer && (
          <>
            <Legend />
            <AnswerView answer={answer} />
          </>
        )}

        {!loading && !error && !answer && (
          <div className={styles.idle}>
            <p>Enter a question or pick an example above.</p>
          </div>
        )}
      </main>

      {globalGraphOpen && (
        <GlobalGraphExplorer
          onClose={() => setGlobalGraphOpen(false)}
          graphData={rawGraphData}
        />
      )}
    </SourceViewerProvider>
  );
}


/** Explains the at-a-glance honesty signals the answer view uses. */
function Legend() {
  return (
    <div className={styles.legend}>
      <span className={styles.legendLabel}>Each claim shows its source type:</span>
      <ModeBadge mode="A" />
      <ModeBadge mode="B" />
      <ModeBadge mode="C" />
      <span className={styles.legendSep} aria-hidden>
        ·
      </span>
      <ConfidenceTag confidence="EXTRACTED" />
      <ConfidenceTag confidence="INFERRED" />
    </div>
  );
}

function LoadingState() {
  return (
    <div className={styles.loading} aria-live="polite">
      <div className={styles.spinner} />
      <span>Routing across the modes and grounding the answer…</span>
    </div>
  );
}
