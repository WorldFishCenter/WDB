"use client";

import { useState, useRef, useMemo, useCallback } from "react";
import type { RouterAnswer, Claim, Mode } from "@/lib/contract";
import { MODE_LABEL } from "@/lib/contract";
import { ClaimCard } from "./ClaimCard";
import { ModeBadge } from "./chips";
import styles from "./panes.module.scss";

/**
 * Claims grouped by source mode in collapsible accordions, with a summary bar above.
 * Replaces the old vertical card stack with a compact, scannable layout.
 * Each mode group renders its claims in a responsive multi-column masonry grid.
 */
export function ClaimsSection({ claims }: { claims: Claim[] }) {
  // Group claims by mode
  const grouped = useMemo(() => {
    const groups: Record<Mode, Claim[]> = { A: [], B: [], C: [] };
    claims.forEach((c) => {
      if (groups[c.mode]) groups[c.mode].push(c);
    });
    return groups;
  }, [claims]);

  // Modes with claims, sorted by count (most claims first)
  const activeModes = useMemo(() => {
    return (Object.entries(grouped) as [Mode, Claim[]][])
      .filter(([, arr]) => arr.length > 0)
      .sort((a, b) => b[1].length - a[1].length)
      .map(([mode]) => mode);
  }, [grouped]);

  // Track which accordion sections are open — default: the mode with most claims
  const [openModes, setOpenModes] = useState<Set<Mode>>(() => {
    return new Set(activeModes.length > 0 ? [activeModes[0]] : []);
  });

  // Refs for scrolling to sections
  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  const toggleMode = useCallback((mode: Mode) => {
    setOpenModes((prev) => {
      const next = new Set(prev);
      if (next.has(mode)) {
        next.delete(mode);
      } else {
        next.add(mode);
      }
      return next;
    });
  }, []);

  const jumpToMode = useCallback((mode: Mode) => {
    // Open the accordion if not already open
    setOpenModes((prev) => {
      const next = new Set(prev);
      next.add(mode);
      return next;
    });
    // Scroll to the section
    setTimeout(() => {
      sectionRefs.current[mode]?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 50);
  }, []);

  if (claims.length === 0) {
    return (
      <div className={styles.empty}>
        No grounded claims for this question — see what wasn&apos;t grounded below.
      </div>
    );
  }

  const MODE_COLORS: Record<Mode, string> = {
    A: "var(--wf-mode-a)",
    B: "var(--wf-mode-b)",
    C: "var(--wf-mode-c)",
  };

  const MODE_BG_COLORS: Record<Mode, string> = {
    A: "var(--wf-mode-a-bg)",
    B: "var(--wf-mode-b-bg)",
    C: "var(--wf-mode-c-bg)",
  };

  return (
    <>
      {/* ── Summary Bar ── */}
      <div className={styles.summaryBar}>
        <span className={styles.summaryLabel}>Claims by source</span>
        {activeModes.map((mode) => (
          <button
            key={mode}
            className={`${styles.summaryChip} ${openModes.has(mode) ? styles.summaryChipActive : ""}`}
            style={{
              background: MODE_BG_COLORS[mode],
              color: MODE_COLORS[mode],
            }}
            onClick={() => jumpToMode(mode)}
            aria-label={`Jump to ${MODE_LABEL[mode]} claims`}
          >
            {MODE_LABEL[mode]}
            <span className={styles.summaryChipCount}>
              {grouped[mode].length}
            </span>
          </button>
        ))}
        <span className={styles.summaryTotal}>
          {claims.length} total
        </span>
      </div>

      {/* ── Mode Accordions ── */}
      {activeModes.map((mode) => {
        const isOpen = openModes.has(mode);
        const modeClaims = grouped[mode];
        return (
          <div
            key={mode}
            className={styles.accordion}
            ref={(el) => { sectionRefs.current[mode] = el; }}
          >
            <button
              className={styles.accordionHeader}
              onClick={() => toggleMode(mode)}
              aria-expanded={isOpen}
              aria-controls={`claims-panel-${mode}`}
            >
              <span
                className={`${styles.accordionChevron} ${isOpen ? styles.accordionChevronOpen : ""}`}
              >
                ▸
              </span>
              <span
                className={styles.accordionModeLine}
                style={{ background: MODE_COLORS[mode] }}
              />
              <ModeBadge mode={mode} />
              <span className={styles.accordionTitle}>
                {MODE_LABEL[mode]}
              </span>
              <span className={styles.accordionCount}>
                {modeClaims.length} {modeClaims.length === 1 ? "claim" : "claims"}
              </span>
            </button>

            {isOpen && (
              <div className={styles.accordionContent} id={`claims-panel-${mode}`}>
                <div className={styles.claimsGrid}>
                  {modeClaims.map((c, i) => (
                    <div key={i} className={styles.claimsGridItem}>
                      <ClaimCard claim={c} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </>
  );
}

/**
 * Backwards-compatible export: the old AnswerPane wrapper, now delegating to ClaimsSection.
 * Kept so AnswerView can import it without a rename.
 */
export function AnswerPane({ answer }: { answer: RouterAnswer }) {
  return <ClaimsSection claims={answer.claims} />;
}
