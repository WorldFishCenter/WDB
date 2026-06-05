---
description: Validate a table's shape (tidy wide/long) and fill its data-dictionary value domains via the dict-enricher agent
argument-hint: "[path to a .csv/.xlsx] (optional — defaults to your new/changed tabular files)"
---
Use the dict-enricher subagent on the table(s) in $ARGUMENTS (or my new/changed `.csv`/`.xlsx`
files if none given). First **validate the shape** with `.claude/scripts/dict_enricher.py`: if a
file isn't a tidy single table (wide or long), stop and tell me exactly what to reshape — don't
edit my data. If it's valid, **merge the script's value-domain facts into the matching
`_dict.md`** (`## Columns`), keeping the existing prose meaning and using per-parameter summaries
for long data. Then report the result and remind me this is maintainer-reviewed and that I still
commit source files only and open a PR. Run this as the data-validity check before opening a PR.
