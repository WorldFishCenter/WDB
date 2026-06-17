"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import styles from "./source.module.scss";

interface SourceState {
  path: string;
  loading: boolean;
  text?: string;
  error?: string;
  viewable: boolean;
}

interface SourceViewerCtx {
  /** Open the read-only viewer for a repo-relative source path. */
  openSource: (path: string) => void;
}

const Ctx = createContext<SourceViewerCtx | null>(null);

export function useSourceViewer(): SourceViewerCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useSourceViewer must be used within <SourceViewerProvider>");
  return ctx;
}

export function SourceViewerProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<SourceState | null>(null);

  const openSource = useCallback((path: string) => {
    setState({ path, loading: true, viewable: true });
    fetch(`/api/source?path=${encodeURIComponent(path)}`)
      .then(async (res) => {
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          setState({
            path,
            loading: false,
            viewable: body?.viewable !== false,
            error: body?.error || `Could not open source (${res.status}).`,
          });
          return;
        }
        setState({ path, loading: false, viewable: true, text: body.text });
      })
      .catch(() => {
        setState({ path, loading: false, viewable: true, error: "Could not reach the source viewer." });
      });
  }, []);

  const close = useCallback(() => setState(null), []);

  useEffect(() => {
    if (!state) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state, close]);

  return (
    <Ctx.Provider value={{ openSource }}>
      {children}
      {state && (
        <div className={styles.overlay} onClick={close} role="dialog" aria-modal="true" aria-label={`Source: ${state.path}`}>
          <div className={styles.panel} onClick={(e) => e.stopPropagation()}>
            <header className={styles.head}>
              <div>
                <div className={styles.eyebrow}>Source</div>
                <code className={styles.path}>{state.path}</code>
              </div>
              <button className={styles.close} onClick={close} aria-label="Close source viewer">
                ✕
              </button>
            </header>
            <div className={styles.body}>
              {state.loading && <p className={styles.muted}>Loading source…</p>}
              {state.error && (
                <div className={styles.notice}>
                  <p>{state.error}</p>
                  {!state.viewable && (
                    <p className={styles.muted}>
                      This source is a binary file (PDF / CSV / image). Its evidence is shown in the
                      citation itself — the verbatim quote (Mode B) or the computed rows (Mode C).
                    </p>
                  )}
                </div>
              )}
              {state.text !== undefined && <pre className={styles.text}>{state.text}</pre>}
            </div>
          </div>
        </div>
      )}
    </Ctx.Provider>
  );
}
