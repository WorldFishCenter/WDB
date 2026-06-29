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
 * so it reads as the SAME product, with an Ask / Contribute / Curate switch. Shows the live status of
 * the real ingestion backend and which role/view you're on.
 */
export function IngestionHeader({ role }: { role: "contributor" | "curator" }) {
  const pathname = usePathname();
  const { currentUser, backendOnline } = useIngestion();
  const who = role === "curator" ? "Curator" : `Contributor · ${currentUser}`;

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
          <span className={s.rolePill} title={backendOnline ? "Ingestion service reachable" : "Ingestion service offline"}>
            <span
              className={s.rolePillDot}
              style={{
                background: backendOnline ? "var(--wf-color-success)" : "var(--wf-color-danger)",
                boxShadow: backendOnline ? "0 0 0 3px rgba(6,214,160,0.2)" : "0 0 0 3px rgba(239,71,111,0.2)",
              }}
              aria-hidden
            />
            ingest · {backendOnline ? "live" : "offline"}
          </span>
          <span className={s.rolePill}>
            <span className={s.rolePillDot} aria-hidden />
            {who}
          </span>
        </div>
      </div>
    </header>
  );
}
