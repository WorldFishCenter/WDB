/**
 * Serialize a structured DraftedNote to the markdown a `<file>_dict.md` / `<file>_context.md`
 * actually is (PROTOCOL §6 Template A/B), with the PROTOCOL §8 provenance frontmatter. Used to show
 * the contributor and curator exactly what would be written to git on sign-off — no hidden state.
 */
import type { DraftedNote, Provenance } from "./types";

function frontmatter(p: Provenance): string {
  // The four PROTOCOL §8 fields, stamped at submission (design §4). On the doc's OWN note — never a
  // synthesis hub (PROTOCOL §6 satellite rule 4).
  return [
    "---",
    `contributor: ${p.contributor}`,
    `author: ${p.author}`,
    `captured_at: ${p.captured_at}`,
    `source_url: ${p.source_url}`,
    "---",
  ].join("\n");
}

export function noteToMarkdown(note: DraftedNote, provenance: Provenance): string {
  const out: string[] = [frontmatter(provenance), "", `# ${note.title}`, "", "## Summary", note.summary];

  if (note.template === "A") {
    out.push("", "## Grain", note.grain ?? "");
    out.push("", "## Columns");
    for (const c of note.columns ?? []) out.push(`- ${c.name}: ${c.meaning} — ${c.domain}`);
  } else {
    out.push("", "## Key concepts / entities");
    for (const k of note.keyConcepts ?? []) out.push(`- ${k}`);
  }

  out.push("", "## Related files");
  for (const r of note.relatedFiles) out.push(`- ${r}`);

  if (note.template === "A" && note.notesCaveats) {
    out.push("", "## Notes / caveats", note.notesCaveats);
  }

  return out.join("\n") + "\n";
}
