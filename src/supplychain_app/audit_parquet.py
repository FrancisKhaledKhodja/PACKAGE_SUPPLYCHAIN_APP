import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import polars as pl
import pyarrow.parquet as pq


@dataclass(frozen=True)
class ColumnProfile:
    name: str
    dtype: str
    null_count_sample: int | None
    n_unique_sample: int | None


@dataclass(frozen=True)
class TableProfile:
    name: str
    path: str
    row_count: int | None
    columns: list[ColumnProfile]
    key_candidates: list[str]


@dataclass(frozen=True)
class RelationshipCandidate:
    from_table: str
    from_column: str
    to_table: str
    to_column: str
    match_rate_sample: float | None
    from_distinct_sample: int | None
    to_distinct_sample: int | None
    to_is_unique_sample: bool | None


def _iter_parquet_files(data_dir: Path) -> list[Path]:
    files: list[Path] = []
    for p in data_dir.rglob("*.parquet"):
        if p.is_file():
            files.append(p)
    return sorted(files)


def _table_name_from_path(path: Path) -> str:
    return path.stem


def _dtype_to_str(dtype: Any) -> str:
    try:
        return str(dtype)
    except Exception:
        return repr(dtype)


def _key_candidate_columns(col_names: Iterable[str]) -> list[str]:
    out: list[str] = []
    for c in col_names:
        lc = c.lower()
        if (
            lc == "id"
            or lc.endswith("_id")
            or lc.endswith("id")
            or lc.endswith("_code")
            or lc.endswith("code")
            or lc.startswith("code_")
            or lc.startswith("cle_")
            or lc.startswith("n_")
        ):
            out.append(c)
    return out


def _profile_table(
    parquet_path: Path,
    max_rows_profile: int,
) -> TableProfile:
    table_name = _table_name_from_path(parquet_path)

    row_count: int | None = None
    arrow_schema = None
    try:
        pf = pq.ParquetFile(parquet_path)
        arrow_schema = pf.schema_arrow
        row_count = pf.metadata.num_rows if pf.metadata is not None else None
    except Exception:
        arrow_schema = None

    if arrow_schema is not None:
        col_names = [f.name for f in arrow_schema]
        col_types = {f.name: _dtype_to_str(f.type) for f in arrow_schema}
    else:
        lf = pl.scan_parquet(str(parquet_path))
        col_names = lf.columns
        col_types = {c: _dtype_to_str(lf.schema.get(c)) for c in col_names}

    key_candidates = _key_candidate_columns(col_names)

    columns: list[ColumnProfile] = []
    lf = pl.scan_parquet(str(parquet_path))
    for c in col_names:
        null_count_sample: int | None = None
        n_unique_sample: int | None = None
        try:
            sample = lf.select(pl.col(c)).limit(max_rows_profile).collect()
            s = sample.get_column(c)
            null_count_sample = int(s.null_count())
            n_unique_sample = int(s.n_unique())
        except Exception:
            null_count_sample = None
            n_unique_sample = None

        columns.append(
            ColumnProfile(
                name=c,
                dtype=col_types.get(c, "unknown"),
                null_count_sample=null_count_sample,
                n_unique_sample=n_unique_sample,
            )
        )

    return TableProfile(
        name=table_name,
        path=str(parquet_path),
        row_count=row_count,
        columns=columns,
        key_candidates=key_candidates,
    )


def _collect_distinct_sample(
    parquet_path: Path,
    column: str,
    max_distinct: int,
    max_rows_scan: int,
) -> pl.DataFrame | None:
    try:
        lf = (
            pl.scan_parquet(str(parquet_path))
            .select(pl.col(column))
            .drop_nulls()
            .limit(max_rows_scan)
            .unique()
            .limit(max_distinct)
        )
        return lf.collect()
    except Exception:
        return None


def _infer_relationships(
    tables: list[TableProfile],
    max_rows_scan: int,
    max_distinct: int,
) -> list[RelationshipCandidate]:
    by_name = {t.name: t for t in tables}
    table_paths = {t.name: Path(t.path) for t in tables}

    table_columns = {t.name: {c.name: c for c in t.columns} for t in tables}

    relationships: list[RelationshipCandidate] = []

    for left in tables:
        for col in left.key_candidates:
            for right in tables:
                if right.name == left.name:
                    continue
                if col not in table_columns[right.name]:
                    continue

                left_dist = _collect_distinct_sample(
                    table_paths[left.name],
                    col,
                    max_distinct=max_distinct,
                    max_rows_scan=max_rows_scan,
                )
                right_dist = _collect_distinct_sample(
                    table_paths[right.name],
                    col,
                    max_distinct=max_distinct,
                    max_rows_scan=max_rows_scan,
                )

                if left_dist is None or right_dist is None:
                    relationships.append(
                        RelationshipCandidate(
                            from_table=left.name,
                            from_column=col,
                            to_table=right.name,
                            to_column=col,
                            match_rate_sample=None,
                            from_distinct_sample=None,
                            to_distinct_sample=None,
                            to_is_unique_sample=None,
                        )
                    )
                    continue

                lcol = left_dist.get_column(col)
                rcol = right_dist.get_column(col)
                from_distinct_sample = int(lcol.len())
                to_distinct_sample = int(rcol.len())

                try:
                    joined = left_dist.join(right_dist, on=col, how="semi")
                    match_rate_sample = float(joined.height / max(1, left_dist.height))
                except Exception:
                    match_rate_sample = None

                right_row_count = by_name[right.name].row_count
                right_is_unique_sample = None
                if right_row_count is not None:
                    rc_sample = to_distinct_sample
                    right_is_unique_sample = bool(rc_sample >= min(max_distinct, right_row_count) and rc_sample > 0)

                relationships.append(
                    RelationshipCandidate(
                        from_table=left.name,
                        from_column=col,
                        to_table=right.name,
                        to_column=col,
                        match_rate_sample=match_rate_sample,
                        from_distinct_sample=from_distinct_sample,
                        to_distinct_sample=to_distinct_sample,
                        to_is_unique_sample=right_is_unique_sample,
                    )
                )

    seen: set[tuple[str, str, str, str]] = set()
    deduped: list[RelationshipCandidate] = []
    for r in relationships:
        k = (r.from_table, r.from_column, r.to_table, r.to_column)
        if k in seen:
            continue
        seen.add(k)
        deduped.append(r)

    deduped.sort(
        key=lambda r: (
            r.from_table,
            r.from_column,
            r.to_table,
            r.to_column,
        )
    )
    return deduped


def build_catalog(
    data_dir: Path,
    out_path: Path,
    max_rows_profile: int = 200_000,
    max_rows_scan: int = 1_000_000,
    max_distinct: int = 20_000,
) -> dict[str, Any]:
    parquet_files = _iter_parquet_files(data_dir)

    tables: list[TableProfile] = []
    for p in parquet_files:
        tables.append(_profile_table(p, max_rows_profile=max_rows_profile))

    relationships = _infer_relationships(
        tables=tables,
        max_rows_scan=max_rows_scan,
        max_distinct=max_distinct,
    )

    catalog: dict[str, Any] = {
        "data_dir": str(data_dir),
        "tables": [asdict(t) for t in tables],
        "relationships": [asdict(r) for r in relationships],
        "profiling": {
            "max_rows_profile": max_rows_profile,
            "max_rows_scan": max_rows_scan,
            "max_distinct": max_distinct,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

    return catalog


def _default_data_dir() -> Path:
    try:
        from supplychain_app.constants import folder_name_app, path_datan

        if path_datan and folder_name_app:
            return Path(os.path.join(path_datan, folder_name_app))
    except Exception:
        pass

    env = os.getenv("DATA_DIR")
    if env:
        return Path(env)

    return Path.cwd()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="supplychain_app.audit_parquet")
    parser.add_argument("--data-dir", type=str, default=None)
    parser.add_argument("--out", type=str, default=None)
    parser.add_argument("--max-rows-profile", type=int, default=200_000)
    parser.add_argument("--max-rows-scan", type=int, default=1_000_000)
    parser.add_argument("--max-distinct", type=int, default=20_000)

    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir) if args.data_dir else _default_data_dir()
    out_path = Path(args.out) if args.out else (data_dir / "catalog.json")

    build_catalog(
        data_dir=data_dir,
        out_path=out_path,
        max_rows_profile=args.max_rows_profile,
        max_rows_scan=args.max_rows_scan,
        max_distinct=args.max_distinct,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
