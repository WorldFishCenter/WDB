"""The executor — DuckDB over the committed CSVs, in place.

The engine the first proof (``proof_c/FINDINGS.md``) settled: DuckDB computes the
number precisely and refuses by construction (an absent value yields 0 rows; an
absent column fails to bind). This module turns a gated ``Resolution`` into the
exact SQL the proof would write — crucially **grain-faithful**: when
``grain_key`` is set it collapses to one row per entity before aggregating, so
the trip-grain answer (31.88) is computed, never the raw-row trap (28.99).

Identifiers (table path, column names, grain key, group-by) are validated
against the catalog before any SQL is built; filter *values* are bound as query
parameters. Nothing the resolver emits is interpolated as raw SQL text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import duckdb

from .catalog import Catalog, TableSpec
from .resolution import Op, Resolution

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_VALID_AGG = {"AVG", "COUNT", "SUM", "MIN", "MAX"}


class ExecutionError(Exception):
    """A resolution that cannot be turned into safe SQL (caught upstream)."""


@dataclass
class ExecResult:
    sql: str
    rows: list[dict]

    @property
    def empty(self) -> bool:
        if not self.rows:
            return True
        # single-row aggregate with no matches -> n == 0 -> not available
        first = self.rows[0]
        return "n" in first and first["n"] == 0


def _check_ident(name: str, allowed: set[str], kind: str) -> str:
    if name not in allowed or not _IDENT_RE.match(name):
        raise ExecutionError(f"{kind} {name!r} is not a known column/identifier")
    return name


def _value_expr(res: Resolution) -> str:
    agg = res.aggregation.upper()
    if agg not in _VALID_AGG:
        raise ExecutionError(f"unsupported aggregation {res.aggregation!r}")
    if agg == "COUNT":
        return "COUNT(*)"
    if res.derived_formula:
        metric = res.derived_formula            # validated below against derived_inputs
    elif res.metric_column:
        metric = res.metric_column
    else:
        raise ExecutionError("no metric to aggregate")
    return f"ROUND({agg}({metric}), {int(res.round_digits)})"


def _validate_derived_formula(res: Resolution) -> None:
    """The derived formula may reference ONLY its declared input columns + SQL safe tokens."""
    if not res.derived_formula:
        return
    # strip declared inputs and a small allowlist of arithmetic / NULLIF tokens,
    # then ensure nothing alphabetic remains (no stray identifiers / functions).
    expr = res.derived_formula
    for col in res.derived_inputs:
        expr = re.sub(rf"\b{re.escape(col)}\b", " ", expr)
    expr = re.sub(r"\bNULLIF\b", " ", expr, flags=re.IGNORECASE)
    if re.search(r"[A-Za-z]", expr):
        raise ExecutionError(
            f"derived formula references tokens beyond its declared inputs: {res.derived_formula!r}"
        )


def build_sql(res: Resolution, spec: TableSpec, abs_path: str) -> tuple[str, list]:
    if "'" in abs_path:
        raise ExecutionError("table path contains an unsafe quote")
    cols = set(spec.columns)
    label = res.metric_label if _IDENT_RE.match(res.metric_label or "") else "value"
    _validate_derived_formula(res)
    for c in res.columns_used():
        _check_ident(c, cols, "column")
    if res.grain_key is not None:
        _check_ident(res.grain_key, cols, "grain key")

    where, params = _build_where(res, spec)
    value_expr = _value_expr(res)
    src = f"read_csv_auto('{abs_path}')"

    # grouped comparison (figure data): one row per group, NULL group dropped
    if res.group_by:
        gb = _check_ident(res.group_by, cols, "group-by")
        not_null = f"{gb} IS NOT NULL"
        where = (where + f"  AND {not_null}\n") if where else f"WHERE {not_null}\n"
        if res.grain_key:
            select = ", ".join(f"ANY_VALUE({c}) AS {c}" for c in sorted(res.columns_used()))
            inner = (
                f"WITH grain AS (\n  SELECT {res.grain_key} AS {res.grain_key}, {select}\n"
                f"  FROM {src}\n  GROUP BY {res.grain_key}\n)"
            )
            from_ = "grain"
        else:
            inner, from_ = "", src
        sql = (
            f"{inner}\nSELECT {gb}, COUNT(*) AS n, {value_expr} AS {label}\n"
            f"FROM {from_}\n{where}GROUP BY {gb}\nORDER BY {label} DESC"
        ).strip()
        return sql, params

    # scalar aggregate (the 9-question shape)
    if res.grain_key:
        select = ", ".join(f"ANY_VALUE({c}) AS {c}" for c in sorted(res.columns_used()))
        sql = (
            f"WITH grain AS (\n  SELECT {res.grain_key} AS {res.grain_key}, {select}\n"
            f"  FROM {src}\n  GROUP BY {res.grain_key}\n)\n"
            f"SELECT COUNT(*) AS n, {value_expr} AS {label}\nFROM grain\n{where}"
        ).strip()
    else:
        sql = (
            f"SELECT COUNT(*) AS n, {value_expr} AS {label}\nFROM {src}\n{where}"
        ).strip()
    return sql, params


def _build_where(res: Resolution, spec: TableSpec) -> tuple[str, list]:
    clauses: list[str] = []
    params: list = []
    for f in res.filters:
        _check_ident(f.column, set(spec.columns), "filter column")
        if f.op is Op.EQ:
            clauses.append(f"{f.column} = ?")
            params.append(f.value)
        elif f.op is Op.CONTAINS:
            clauses.append(f"{f.column} ILIKE ?")
            params.append(f"%{f.value}%")
        else:  # pragma: no cover - exhaustive
            raise ExecutionError(f"unsupported filter op {f.op!r}")
    where = ("WHERE " + " AND ".join(clauses) + "\n") if clauses else ""
    return where, params


def execute(res: Resolution, catalog: Catalog) -> ExecResult:
    spec = catalog.get(res.table)
    if spec is None:
        raise ExecutionError(f"unknown table {res.table!r}")
    abs_path = catalog.abs_path(res.table)
    sql, params = build_sql(res, spec, abs_path)
    con = duckdb.connect()  # in-memory; the CSV is read in place, never copied
    try:
        rel = con.execute(sql, params)
        names = [d[0] for d in rel.description]
        rows = [
            {name: _scalar(v) for name, v in zip(names, row)}
            for row in rel.fetchall()
        ]
    finally:
        con.close()
    return ExecResult(sql=sql, rows=rows)


def _scalar(v):
    # ROUND already applied in SQL; coerce DuckDB Decimals to float for clean JSON
    try:
        from decimal import Decimal

        if isinstance(v, Decimal):
            return float(v)
    except Exception:  # pragma: no cover
        pass
    return v
