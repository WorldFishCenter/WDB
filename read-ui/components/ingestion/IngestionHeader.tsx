"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useIngestion } from "@/lib/ingestion/store";
import s from "./ingestion.module.scss";

const NAV = [
  { href: "/", label: "Ask", icon: "◎" },
  { href: "/contribute", label: "Contribute", icon: "✎" },
  { href: "/curate", label: "Curate", icon: "✓" },
];

/**
 * The ingestion app bar — reuses the read UI's header chrome (same blur, brand mark, pill styling)
 * so it reads as the SAME product, with an Ask / Contribute / Curate switch. The role pill names
 * whose surface you're on; the MOCK tag + Reset make the prototype nature honest.
 */
export function IngestionHeader({ role }: { role: "contributor" | "curator" }) {
  const pathname = usePathname();
  const { currentContributor, resetDemo } = useIngestion();
  const who = role === "curator" ? "Curator" : `Contributor · ${currentContributor}`;

  return (
    <header className={s.bar}>
      <div className={`wf-container ${s.barInner}`}>
        <div className={s.brand}>
          <span className={s.mark}>WDB</span>
          <span className={s.brandText}>WorldFish Digital Brain</span>
        </div>

        <nav className={s.nav}>
          {NAV.map((n) => {
            const active = n.href === "/" ? pathname === "/" : pathname.startsWith(n.href);
            return (
              <Link key={n.href} href={n.href} className={`${s.navLink} ${active ? s.navLinkActive : ""}`}>
                <span className={s.navIcon} aria-hidden>{n.icon}</span>
                {n.label}
              </Link>
            );
          })}
        </nav>

        <div className={s.barRight}>
          <span className={s.mockTag} title="This is a styled prototype against mock data — no ingestion backend is wired yet.">
            prototype · mock data
          </span>
          <span className={s.rolePill}>
            <span className={s.rolePillDot} aria-hidden />
            {who}
          </span>
          <button className={s.resetBtn} onClick={resetDemo} title="Reset the mock workflow to its seed state">
            Reset
          </button>
        </div>
      </div>
    </header>
  );
}
