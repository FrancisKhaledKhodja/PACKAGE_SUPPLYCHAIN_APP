import polars as pl
from supplychain_app.services.pudo_service import (
    search_items_advanced,
    get_item_by_code,
    get_manufacturers_for,
    get_equivalents_for,
    stats_exit_items,
    stats_exit_items_monthly,
)

def search_items_df(q: str, filters: dict, limit: int) -> pl.DataFrame | None:
    return search_items_advanced(q, filters, max_rows=limit)

def get_item_full(code: str) -> dict:
    return {
        "item": get_item_by_code(code),
        "manufacturers": get_manufacturers_for(code),
        "equivalents": get_equivalents_for(code),
    }

def get_stats_exit(code: str, type_exit: str | list[str] | None = None) -> pl.DataFrame:
    return stats_exit_items(code, type_exit)

def get_stats_exit_monthly(code: str, type_exit: str | list[str] | None = None) -> pl.DataFrame:
    return stats_exit_items_monthly(code, type_exit)

