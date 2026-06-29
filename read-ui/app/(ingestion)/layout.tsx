"use client";

import { IngestionProvider } from "@/lib/ingestion/store";

/**
 * Route-group layout for the ingestion (write-side) views. Mounting the IngestionProvider here —
 * shared by /contribute and /curate — means the mock workflow state is ONE store across both views:
 * a contributor approval in /contribute shows up in the curator queue in /curate without a reload.
 * The group "(ingestion)" doesn't affect the URLs (routes stay /contribute and /curate).
 */
export default function IngestionLayout({ children }: { children: React.ReactNode }) {
  return <IngestionProvider>{children}</IngestionProvider>;
}
