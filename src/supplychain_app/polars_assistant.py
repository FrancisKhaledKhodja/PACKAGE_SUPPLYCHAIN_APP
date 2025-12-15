import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl


@dataclass(frozen=True)
class PolarsPlan:
    intent: str
    tables: list[str]
    joins: list[dict[str, Any]]
    filters: list[dict[str, Any]]
    selected_columns: list[str]
    preview_rows: int


def _default_data_dir() -> Path:
    env = os.getenv("DATA_DIR")
    if env:
        return Path(env)

    try:
        from supplychain_app.constants import folder_name_app, path_datan

        return Path(path_datan) / folder_name_app
    except Exception:
        return Path.cwd()


def _scan_table(data_dir: Path, table: str) -> pl.LazyFrame:
    path = data_dir / f"{table}.parquet"
    return pl.scan_parquet(str(path))


def _existing_columns(lf: pl.LazyFrame, candidates: list[str]) -> list[str]:
    schema = lf.schema
    return [c for c in candidates if c in schema]


def build_stock_by_store_plan(preview_rows: int) -> PolarsPlan:
    tables = ["minmax", "stock_final", "stores", "items"]
    joins = [
        {"left": "minmax", "right": "stock_final", "on": ["code_magasin", "code_article"], "how": "left"},
        {"left": "minmax", "right": "stores", "on": ["code_magasin"], "how": "left"},
        {"left": "minmax", "right": "items", "on": ["code_article"], "how": "left"},
    ]
    filters: list[dict[str, Any]] = []
    selected_columns = [
        "code_article",
        "libelle_court_article",
        "libelle_long_article",
        "code_magasin",
        "libelle_magasin",
        "qte_min",
        "qte_max",
        "qte_stock",
        "valo_stock",
        "categorie_sans_sortie",
        "nbre_jours_sans_sortie",
        "delai_anciennete_jours",
        "categorie_anciennete",
    ]
    return PolarsPlan(
        intent="stock_by_store",
        tables=tables,
        joins=joins,
        filters=filters,
        selected_columns=selected_columns,
        preview_rows=int(preview_rows),
    )


def build_stock_article_plan(code_article: str, preview_rows: int) -> PolarsPlan:
    tables = ["stock_554", "stores", "items"]
    joins = [
        {"left": "stock_554", "right": "stores", "on": ["code_magasin"], "how": "left"},
        {"left": "stock_554", "right": "items", "on": ["code_article"], "how": "left"},
    ]
    filters = [
        {"column": "code_article", "op": "=", "value": code_article},
    ]
    selected_columns = [
        "code_article",
        "libelle_court_article",
        "libelle_long_article",
        "code_magasin",
        "libelle_magasin",
        "qte_stock",
        "valo_stock",
        "n_lot",
        "n_serie",
        "qualite",
        "date_reception",
    ]
    return PolarsPlan(
        intent="stock_article",
        tables=tables,
        joins=joins,
        filters=filters,
        selected_columns=selected_columns,
        preview_rows=int(preview_rows),
    )


def build_equivalent_article_plan(code_article: str, preview_rows: int) -> PolarsPlan:
    # Remarque: la colonne correcte est type_de_relation.
    tables = ["equivalents", "items"]
    joins = [
        {
            "left": "equivalents",
            "right": "items",
            "left_on": ["code_article_correspondant"],
            "right_on": ["code_article"],
            "how": "left",
        },
    ]
    filters = [
        {
            "any": [
                {"column": "code_article", "op": "=", "value": code_article},
                {"column": "code_article_origine", "op": "=", "value": code_article},
            ]
        },
        {
            "any": [
                {"column": "type_de_relation", "op": "=", "value": "Substitution"},
            ]
        },
    ]
    selected_columns = [
        "code_article",
        "code_article_correspondant",
        "type_de_relation",
        "libelle_court_article",
        "libelle_long_article",
    ]
    return PolarsPlan(
        intent="equivalent_article",
        tables=tables,
        joins=joins,
        filters=filters,
        selected_columns=selected_columns,
        preview_rows=int(preview_rows),
    )


def _extract_code_article(question: str) -> str | None:
    m = re.search(r"\b(TDF\d{3,}|[A-Z]{2,}\d{3,})\b", question or "", re.IGNORECASE)
    if not m:
        return None
    return m.group(1).upper()


def build_plan_from_question(question: str, preview_rows: int) -> PolarsPlan:
    q = (question or "").lower()
    code_article = _extract_code_article(question)

    if code_article and any(k in q for k in ("equivalent", "équivalent", "equivalence", "substitution", "substituer", "remplacement")):
        return build_equivalent_article_plan(code_article=code_article, preview_rows=preview_rows)

    if "stock" in q and code_article:
        return build_stock_article_plan(code_article=code_article, preview_rows=preview_rows)

    if any(k in q for k in ("stock", "minmax", "magasin", "stores")):
        return build_stock_by_store_plan(preview_rows=preview_rows)

    return build_stock_by_store_plan(preview_rows=preview_rows)


def build_plan_from_rag(question: str, rag_hits: list[dict[str, Any]], preview_rows: int) -> PolarsPlan:
    tables: set[str] = set()
    join_keys: set[str] = set()

    for h in rag_hits or []:
        if not isinstance(h, dict):
            continue
        payload = h.get("payload")
        if not isinstance(payload, dict):
            continue

        if payload.get("type") == "table":
            t = payload.get("table")
            if isinstance(t, str) and t:
                tables.add(t)

        if payload.get("type") == "join":
            ft = payload.get("from_table")
            tt = payload.get("to_table")
            fc = payload.get("from_column")
            tc = payload.get("to_column")
            for t in (ft, tt):
                if isinstance(t, str) and t:
                    tables.add(t)
            if isinstance(fc, str):
                join_keys.add(fc)
            if isinstance(tc, str):
                join_keys.add(tc)

    q = (question or "").lower()
    code_article = _extract_code_article(question)
    wants_stock = any(k in q for k in ("stock", "minmax", "magasin", "stores", "valo", "valorisation"))

    if code_article and any(k in q for k in ("equivalent", "équivalent", "equivalence", "substitution", "substituer", "remplacement")):
        return build_equivalent_article_plan(code_article=code_article, preview_rows=preview_rows)

    if "stock" in q and code_article:
        # Règle déterministe : "quel est le stock du TDFxxxx" => stock_554 filtré sur code_article
        return build_stock_article_plan(code_article=code_article, preview_rows=preview_rows)

    if wants_stock or {"minmax", "stock_final", "stores"}.issubset(tables) or ("code_magasin" in join_keys):
        preview_rows = int(preview_rows)
        if preview_rows < 1:
            preview_rows = 1
        if preview_rows > 2000:
            preview_rows = 2000

        base_tables = {"minmax", "stock_final", "stores"}
        if "code_article" in join_keys or "items" in tables:
            base_tables.add("items")

        out_tables = sorted(base_tables)
        joins: list[dict[str, Any]] = []
        if "stock_final" in base_tables:
            joins.append({"left": "minmax", "right": "stock_final", "on": ["code_magasin", "code_article"], "how": "left"})
        if "stores" in base_tables:
            joins.append({"left": "minmax", "right": "stores", "on": ["code_magasin"], "how": "left"})
        if "items" in base_tables:
            joins.append({"left": "minmax", "right": "items", "on": ["code_article"], "how": "left"})

        selected_columns = build_stock_by_store_plan(preview_rows=preview_rows).selected_columns
        return PolarsPlan(
            intent="stock_by_store",
            tables=out_tables,
            joins=joins,
            filters=[],
            selected_columns=selected_columns,
            preview_rows=preview_rows,
        )

    return build_plan_from_question(question=question, preview_rows=preview_rows)


def compile_plan_to_lazyframe(plan: PolarsPlan, data_dir: Path) -> pl.LazyFrame:
    lfs: dict[str, pl.LazyFrame] = {t: _scan_table(data_dir, t) for t in plan.tables}

    if plan.intent == "stock_by_store":
        base_name = "minmax"
    else:
        base_name = plan.tables[0] if plan.tables else ""
    base = lfs.get(base_name)
    if base is None:
        raise ValueError(f"missing_base_table_{base_name}")

    lf = base

    for j in plan.joins:
        left = j.get("left")
        right = j.get("right")
        on = j.get("on")
        left_on = j.get("left_on")
        right_on = j.get("right_on")
        how = j.get("how") or "left"

        if left != base_name:
            continue

        has_on = isinstance(on, list) and bool(on)
        has_lr = isinstance(left_on, list) and bool(left_on) and isinstance(right_on, list) and bool(right_on)
        if not has_on and not has_lr:
            continue

        rlf = lfs.get(str(right))
        if rlf is None:
            continue

        if has_lr:
            lf = lf.join(
                rlf,
                left_on=left_on,
                right_on=right_on,
                how=how,
                suffix=f"__{right}",
            )
        else:
            lf = lf.join(rlf, on=on, how=how, suffix=f"__{right}")

    for flt in plan.filters or []:
        if not isinstance(flt, dict):
            continue

        any_group = flt.get("any")
        if isinstance(any_group, list):
            expr = None
            for sub in any_group:
                if not isinstance(sub, dict):
                    continue
                col = sub.get("column")
                op = sub.get("op")
                val = sub.get("value")
                if not isinstance(col, str) or col not in lf.schema:
                    continue
                if op == "=":
                    subexpr = pl.col(col) == val
                else:
                    continue
                expr = subexpr if expr is None else (expr | subexpr)
            if expr is not None:
                lf = lf.filter(expr)
            continue

        col = flt.get("column")
        op = flt.get("op")
        val = flt.get("value")
        if not isinstance(col, str) or col not in lf.schema:
            continue
        if op == "=":
            lf = lf.filter(pl.col(col) == val)

    cols = _existing_columns(lf, plan.selected_columns)
    if cols:
        lf = lf.select(cols)

    return lf


def compile_plan_to_polars_code(plan: PolarsPlan, data_dir: Path) -> str:
    dd = str(data_dir).replace("\\", "\\\\")

    lines: list[str] = []
    lines.append("import polars as pl")
    lines.append(f"data_dir = r\"{dd}\"")
    for t in plan.tables:
        lines.append(f"{t} = pl.scan_parquet(f\"{data_dir}\\\\{t}.parquet\")")

    base_name = "minmax" if plan.intent == "stock_by_store" else (plan.tables[0] if plan.tables else "")
    lines.append(f"lf = {base_name}")
    for j in plan.joins:
        left = j.get("left")
        right = j.get("right")
        on = j.get("on")
        left_on = j.get("left_on")
        right_on = j.get("right_on")
        how = j.get("how") or "left"
        if left != base_name:
            continue
        if not isinstance(right, str):
            continue
        has_on = isinstance(on, list) and bool(on)
        has_lr = isinstance(left_on, list) and bool(left_on) and isinstance(right_on, list) and bool(right_on)
        if has_lr:
            lines.append(
                f"lf = lf.join({right}, left_on={left_on!r}, right_on={right_on!r}, how={how!r}, suffix='__{right}')"
            )
        elif has_on:
            lines.append(
                f"lf = lf.join({right}, on={on!r}, how={how!r}, suffix='__{right}')"
            )

    for flt in plan.filters or []:
        any_group = flt.get("any") if isinstance(flt, dict) else None
        if isinstance(any_group, list) and any_group:
            parts: list[str] = []
            for sub in any_group:
                if not isinstance(sub, dict):
                    continue
                col = sub.get("column")
                op = sub.get("op")
                val = sub.get("value")
                if isinstance(col, str) and op == "=":
                    parts.append(f"(pl.col({col!r}) == {val!r})")
            if parts:
                expr = " | ".join(parts)
                lines.append(f"lf = lf.filter({expr})")
            continue

        if not isinstance(flt, dict):
            continue
        col = flt.get("column")
        op = flt.get("op")
        val = flt.get("value")
        if isinstance(col, str) and op == "=":
            lines.append(f"lf = lf.filter(pl.col({col!r}) == {val!r})")

    cols = plan.selected_columns
    cols_repr = "[" + ", ".join(repr(c) for c in cols) + "]"
    lines.append(f"wanted_cols = {cols_repr}")
    lines.append("existing_cols = [c for c in wanted_cols if c in lf.schema]")
    lines.append("if existing_cols:")
    lines.append("    lf = lf.select(existing_cols)")
    lines.append(f"df = lf.limit({int(plan.preview_rows)}).collect()")
    lines.append("print(df)")

    return "\n".join(lines)
