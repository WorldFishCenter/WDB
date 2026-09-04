"use client";

import type { RouterAnswer } from "@/lib/contract";
import { AnswerPane } from "./AnswerPane";
import { AssociationsPane } from "./AssociationsPane";
import { EntityView } from "./EntityView";
import { Refusal } from "./Refusal";
import { ExplorationProvider, useExploration } from "@/lib/exploration";
import { useGraphData } from "@/lib/graphData";
import styles from "./answerview.module.scss";

/**
 * The balanced dual-view: the question echoes full-width, then the answer (left) and the
 * knowledge-graph stage (right) sit as co-equal, co-primary panes that drive each other through
 * shared state (ExplorationProvider). Hovering a citation lights its nodes in the graph; clicking
 * a node reframes the left pane to that entity. The answer column scrolls; the graph stays in view.
 *
 * An answer that grounded nothing renders as a full-width panel instead — but WHICH panel
 * depends on `verdict`, not on counting empty lists. A VERIFIED_NEGATIVE ("the graph records no
 * connection") is a correct answer and says so; only UNGROUNDED is a coverage refusal.
 */
export function AnswerView({ answer }: { answer: RouterAnswer }) {
  // Branch on the verdict the router computed — never re-infer it from empty payloads.
  const nothingRendered = answer.claims.length === 0 && answer.figures.length === 0;

  if (nothingRendered && answer.verdict !== "GROUNDED") {
    return (
      <div className={styles.wrap}>
        <QuestionEcho question={answer.question} />
        <Refusal answer={answer} />
      </div>
    );
  }

  return (
    <div className={styles.wrap}>
      <QuestionEcho question={answer.question} />
      {/* key by question: a new answer is a fresh exploration (focus + graph reset). */}
      <ExplorationProvider key={answer.question}>
        <Workspace answer={answer} />
      </ExplorationProvider>
    </div>
  );
}

/** The two co-equal panes. The left swaps to the entity view when a graph node is in focus. */
function Workspace({ answer }: { answer: RouterAnswer }) {
  const { focusEntity } = useExploration();
  const { graph, nodeMeta, graphError } = useGraphData();

  return (
    <>
      {/* A graph that failed to load is stated, not shown as an empty stage. The commonest
          cause is a knowledge base the server could not locate (WDB_KB) — see lib/kbRoot.ts.
          It sits ABOVE the two-column grid so it spans the full width. */}
      {graphError && (
        <div role="status" className={styles.graphNotice}>
          <strong>Knowledge graph unavailable.</strong> {graphError} The answer and its citations
          are unaffected.
        </div>
      )}
      <div className={styles.workspace}>
        <div className={styles.answerCol}>
          {focusEntity ? (
            <EntityView entityId={focusEntity} graph={graph} nodeMeta={nodeMeta} />
          ) : (
            <AnswerPane answer={answer} />
          )}
        </div>
        <div className={styles.graphCol}>
          <AssociationsPane associations={answer.associations} graph={graph} nodeMeta={nodeMeta} />
        </div>
      </div>
    </>
  );
}

function QuestionEcho({ question }: { question: string }) {
  return (
    <div className={styles.echo}>
      <span className={styles.echoLabel}>Question</span>
      <span className={styles.echoText}>{question}</span>
    </div>
  );
}
