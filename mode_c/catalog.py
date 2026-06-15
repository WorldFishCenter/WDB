"""The catalog — the structural contract Mode C routes and gates against.

Reads every ``*_dict.md`` companion note in the WDB repo (the ones ``/enrich``
writes, per PROTOCOL §5-6 Template A) and extracts, per tidy table:

* its ``## Columns`` value domains (the candidate routing key, §4.3 of the
  three-mode architecture doc),
* its explicit ``## Grain`` line (Phase 0): the dedup key and which columns are
  higher-grain attributes that *repeat* across rows — what the vetted-band gate
  needs to make the grain trap structurally impossible to pass, and
* identity tokens (initiative / filename) used to pin a table by place or name.

Everything here is deterministic and offline — it is the same committed data the
graph and the proof read in place.
"""

from __future__ import annotations

import glob
import os
import re
from dataclasses import dataclass, field

# filename / folder words that don't identify a real-world entity
_IDENTITY_STOPWORDS = {
    "validated", "trips", "data", "database", "composition", "feed", "ingredient",
    "observations", "wide", "long", "measurements", "tanks", "reference", "quality",
    "specification", "nutrition", "practical", "aquaculture", "formulation",
    "calculated", "formulations", "accelerator", "transformation", "digital",
    "feed_ingredient",
}


@dataclass(frozen=True)
class Column:
    name: str
    body: str                         # the full bullet body after "name:" (for rendering)
    match_text: str                   # lowercased body (for substring routing)
    categorical: tuple[str, ...] = ()  # enumerated members parsed from "∈ {a, b, c}"
    examples: tuple[str, ...] = ()      # backticked example values (e.g. `crude_protein_percent`)


@dataclass
class TableSpec:
    table: str                        # WDB-relative CSV path
    dict_file: str                    # WDB-relative dict path
    summary: str
    columns: dict[str, Column]
    grain_text: str                   # full ## Grain block ("" if absent / unreviewed)
    grain_key: str | None             # dedup key parsed from grain ("trip_id"), if any
    repeating_columns: frozenset[str]  # columns the grain marks as higher-grain / repeating
    identity_tokens: frozenset[str]    # initiative / filename tokens that pin this table

    @property
    def has_grain(self) -> bool:
        return bool(self.grain_text.strip())


@dataclass
class Catalog:
    tables: dict[str, TableSpec]       # keyed by WDB-relative CSV path
    root: str

    def get(self, table: str) -> TableSpec | None:
        return self.tables.get(table)

    def abs_path(self, table: str) -> str:
        return os.path.join(self.root, table)

    def pin_table(self, value: str) -> set[str]:
        """Tables for which ``value`` is a *distinctive* identifier.

        A table matches when ``value`` (case-insensitive) is an exact member of
        one of its categorical domains, an identity token (initiative/filename),
        or — for multi-word phrases like "fish meal" — a substring of a column's
        value-domain text. The vetted-band gate calls this to verify a value
        pins exactly one table.
        """
        v = value.casefold().strip()
        multiword = " " in v
        hits: set[str] = set()
        for spec in self.tables.values():
            if v in {t.casefold() for t in spec.identity_tokens}:
                hits.add(spec.table)
                continue
            matched = False
            for col in spec.columns.values():
                if any(v == m.casefold() for m in col.categorical):
                    matched = True
                    break
                if any(v == ex.casefold() for ex in col.examples):
                    matched = True
                    break
                if multiword and v in col.match_text:
                    matched = True
                    break
            if matched:
                hits.add(spec.table)
        return hits

    def render_corpus(self) -> str:
        """The catalog text the resolver prompt embeds (one source of truth: the dicts)."""
        parts = ["# WDB data catalog — the ONLY tables you may route to\n"]
        for spec in self.tables.values():
            parts.append(f"\n==================== TABLE: {spec.table} ====================")
            parts.append(f"## Summary\n{spec.summary}\n")
            parts.append("## Columns")
            for col in spec.columns.values():
                parts.append(f"- {col.name}: {col.body}")
            if spec.grain_text:
                parts.append(f"\n## Grain\n{spec.grain_text}")
        return "\n".join(parts)


# --------------------------------------------------------------------------- #
# parsing
# --------------------------------------------------------------------------- #

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def _split_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(text))
    for i, m in enumerate(matches):
        name = m.group(1).strip().lower()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        sections[name] = text[start:end].strip()
    return sections


def _parse_columns(block: str) -> dict[str, Column]:
    cols: dict[str, Column] = {}
    for raw in block.splitlines():
        line = raw.strip()
        if not line.startswith("- "):
            continue
        body = line[2:]
        if ":" not in body:
            continue
        name, rest = body.split(":", 1)
        name = name.strip().strip("`*")
        rest = rest.strip()
        members = ()
        dm = re.search(r"∈\s*\{([^}]*)\}", rest)
        if dm:
            members = tuple(m.strip().strip("`") for m in dm.group(1).split(",") if m.strip())
        examples = tuple(re.findall(r"`([^`]+)`", rest))
        cols[name] = Column(
            name=name,
            body=rest,
            match_text=rest.casefold(),
            categorical=members,
            examples=examples,
        )
    return cols


def _parse_grain(block: str) -> tuple[str | None, frozenset[str]]:
    """Return (grain_key, repeating_columns) parsed from a ## Grain block.

    Handles both Phase-0 templates: the trip tables' plain list
    ("...repeating across its catch rows are A, B, C — aggregate over distinct
    `trip_id`...") and FICD's backticked form ("descriptors `code` and
    `description` repeat across...").
    """
    flat = re.sub(r"\s+", " ", block)
    key = None
    m = re.search(r"over distinct `?(\w+)`?", flat)
    if m:
        key = m.group(1)
    else:
        m = re.search(r"finer than `?(\w+)`?", flat)
        if m:
            key = m.group(1)

    repeating: set[str] = set()
    # plain comma list between "repeating across ... are" and the em dash
    m = re.search(r"repeating across[^—]*?\bare\b\s*(.+?)\s*—", flat)
    if m:
        for tok in m.group(1).split(","):
            tok = tok.strip().strip("`")
            if re.fullmatch(r"\w+", tok):
                repeating.add(tok)
    # backticked identifiers in any sentence mentioning "repeat"
    for sent in re.split(r"(?<=[.;]) ", flat):
        if "repeat" in sent.lower():
            repeating.update(re.findall(r"`(\w+)`", sent))
    # never treat the grain key itself as a repeating attribute
    repeating.discard(key or "")
    return key, frozenset(repeating)


def _identity_tokens(table_rel: str) -> frozenset[str]:
    stem = os.path.basename(table_rel)
    stem = re.sub(r"\.csv$", "", stem)
    parts = re.split(r"[._]", stem)
    folder_parts = re.split(r"[._/]", os.path.dirname(table_rel))
    tokens = {
        p.casefold()
        for p in (*parts, *folder_parts)
        if p and p.casefold() not in _IDENTITY_STOPWORDS
    }
    return frozenset(tokens)


def load_catalog(root: str | None = None) -> Catalog:
    """Load every tidy table's ``_dict.md`` into a :class:`Catalog`."""
    if root is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tables: dict[str, TableSpec] = {}
    for path in sorted(glob.glob(os.path.join(root, "**", "*_dict.md"), recursive=True)):
        if "graphify-out" in path:
            continue
        rel_dict = os.path.relpath(path, root)
        csv_rel = re.sub(r"_dict\.md$", ".csv", rel_dict)
        if not os.path.exists(os.path.join(root, csv_rel)):
            continue  # a _dict.md without its CSV is not a routable table
        text = open(path, encoding="utf-8").read()
        sections = _split_sections(text)
        grain_block = sections.get("grain", "")
        grain_key, repeating = _parse_grain(grain_block)
        tables[csv_rel] = TableSpec(
            table=csv_rel,
            dict_file=rel_dict,
            summary=sections.get("summary", "").strip(),
            columns=_parse_columns(sections.get("columns", "")),
            grain_text=grain_block,
            grain_key=grain_key,
            repeating_columns=repeating,
            identity_tokens=_identity_tokens(csv_rel),
        )
    return Catalog(tables=tables, root=root)
