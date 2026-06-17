"use client";

import { useState } from "react";
import styles from "./queryform.module.scss";

/** The example questions captured in STEP 0 — one per honesty state, so the dual-pane behaviour
 * is one click away (graph-only, computed+figure, full blend, partial blend, honest refusal). */
const EXAMPLES: { label: string; question: string; tag: string }[] = [
  { tag: "A", label: "Projects in Kenya", question: "What projects operate in Kenya?" },
  {
    tag: "C",
    label: "Catch per trip by county",
    question: "Average total catch per trip by county in Kenya?",
  },
  {
    tag: "A+B+C",
    label: "Peskas — datasets, validation & Kwale catch",
    question:
      "Which datasets feed Peskas, how does Peskas validate catch survey data, and what is the average total catch per trip in Kwale?",
  },
  {
    tag: "partial",
    label: "Kenya projects + Mombasa total (partly ungrounded)",
    question: "Which projects operate in Kenya, and what is the total catch landed in Mombasa?",
  },
  {
    tag: "refusal",
    label: "Off-topic (Norway salmon)",
    question: "What is the impact of salmon cage farming on fjord water quality in Norway?",
  },
];

export function QueryForm({
  onSubmit,
  loading,
}: {
  onSubmit: (question: string) => void;
  loading: boolean;
}) {
  const [value, setValue] = useState("");

  function submit(q: string) {
    const trimmed = q.trim();
    if (!trimmed || loading) return;
    onSubmit(trimmed);
  }

  return (
    <div className={styles.form}>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(value);
        }}
      >
        <div className={styles.inputRow}>
          <input
            className={styles.input}
            type="text"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Ask the knowledge base a question…"
            aria-label="Question"
            autoFocus
          />
          <button className={styles.submit} type="submit" disabled={loading || !value.trim()}>
            {loading ? "Asking…" : "Ask"}
          </button>
        </div>
      </form>

      <div className={styles.examples}>
        <span className={styles.examplesLabel}>Try:</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex.question}
            type="button"
            className={styles.chip}
            disabled={loading}
            onClick={() => {
              setValue(ex.question);
              submit(ex.question);
            }}
            title={ex.question}
          >
            <span className={styles.chipTag}>{ex.tag}</span>
            {ex.label}
          </button>
        ))}
      </div>
    </div>
  );
}
