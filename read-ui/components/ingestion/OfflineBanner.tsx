import s from "./ingestion.module.scss";

/**
 * Honest offline state (mirrors the read UI's "API offline" posture): when the ingestion service
 * isn't running, say so and show how to start it — never fabricate data.
 */
export function OfflineBanner() {
  return (
    <div className={`${s.notice} ${s.noticeRejected}`} style={{ marginBottom: "var(--wf-space-5)" }}>
      <span className={s.noticeIcon} aria-hidden>⚠</span>
      <div>
        <div className={s.noticeTitle}>Ingestion backend offline</div>
        <div className={s.noticeBody}>
          This page is wired to the real <span className={s.mono}>wdb_ingest</span> service, which isn’t
          reachable. Start it from the repo root:{" "}
          <span className={s.mono}>uv run uvicorn wdb_ingest.app:app --port 8001</span>. Nothing is shown
          until it’s up — this surface never fabricates data.
        </div>
      </div>
    </div>
  );
}
