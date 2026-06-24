"use client";

/**
 * Shared state between the two panes — the architectural spine of the dual-view. The answer and
 * the graph drive each other through one small context:
 *
 *   • focusEntity  — the entity the view is "reframed" to. Set by clicking a node in the graph (or
 *                    a related entity in the entity view); both panes reflect it (graph selects +
 *                    lights it, left pane shows what the graph records about it). null = the answer.
 *   • highlightNodes / clearHighlight — transient pulse. Hovering a citation in the answer lights
 *                    its node(s) in the graph, via an imperative bridge the graph registers (so a
 *                    hover never re-renders the whole graph).
 *
 * Selection state lives here, not in either pane, so neither owns the other.
 */

import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

export interface GraphBridge {
  highlight: (ids: string[]) => void;
  clearHighlight: () => void;
}

interface ExplorationCtx {
  focusEntity: string | null;
  reframeTo: (id: string) => void;
  clearReframe: () => void;
  registerGraph: (bridge: GraphBridge | null) => void;
  highlightNodes: (ids: string[]) => void;
  clearHighlight: () => void;
}

const Ctx = createContext<ExplorationCtx | null>(null);

export function useExploration(): ExplorationCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useExploration must be used within <ExplorationProvider>");
  return c;
}

export function ExplorationProvider({ children }: { children: React.ReactNode }) {
  const [focusEntity, setFocusEntity] = useState<string | null>(null);
  const bridge = useRef<GraphBridge | null>(null);

  const registerGraph = useCallback((b: GraphBridge | null) => {
    bridge.current = b;
  }, []);
  const highlightNodes = useCallback((ids: string[]) => bridge.current?.highlight(ids), []);
  const clearHighlight = useCallback(() => bridge.current?.clearHighlight(), []);
  const reframeTo = useCallback((id: string) => setFocusEntity(id), []);
  const clearReframe = useCallback(() => setFocusEntity(null), []);

  const value = useMemo<ExplorationCtx>(
    () => ({ focusEntity, reframeTo, clearReframe, registerGraph, highlightNodes, clearHighlight }),
    [focusEntity, reframeTo, clearReframe, registerGraph, highlightNodes, clearHighlight],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
