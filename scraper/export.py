"""Export products to Excel (with a summary sheet), CSV or JSON."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

from .parsers import Product

COLUMNS = ["title", "category", "price", "currency", "rating", "in_stock", "stock_count", "reviews", "upc", "url", "image_url"]


def save(products: list[Product], out: str | Path) -> Path:
    out = Path(out)
    ext = out.suffix.lower()
    if ext not in (".xlsx", ".csv", ".json"):
        raise ValueError(f"Unknown format {ext!r}: use .xlsx, .csv or .json")
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [p.to_dict() for p in products]
    if ext == ".json":
        out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    elif ext == ".csv":
        with out.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    else:
        _xlsx(rows, out)
    return out


def summarize(products: list[Product]) -> list[dict]:
    """Per-category stats: count, average / min / max price, average rating, units in stock."""
    groups: dict[str, list[Product]] = defaultdict(list)
    for p in products:
        groups[p.category or "—"].append(p)
    summary = []
    for cat, items in groups.items():
        prices = [p.price for p in items]
        summary.append({
            "category": cat,
            "products": len(items),
            "avg_price": round(sum(prices) / len(prices), 2),
            "min_price": min(prices),
            "max_price": max(prices),
            "avg_rating": round(sum(p.rating for p in items) / len(items), 2),
            "units_in_stock": sum(p.stock_count or 0 for p in items),
        })
    return sorted(summary, key=lambda r: r["products"], reverse=True)


def _sheet(wb: Workbook, title: str, rows: list[dict], columns: list[str], widths: dict[str, int]) -> None:
    ws = wb.create_sheet(title)
    ws.append(columns)
    for r in rows:
        ws.append([r.get(c) for c in columns])
    for i, c in enumerate(columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = widths.get(c, 14)
        ws.cell(1, i).font = Font(bold=True, color="FFFFFF")
        ws.cell(1, i).fill = PatternFill("solid", fgColor="1F4E78")
    if rows:
        ref = f"A1:{get_column_letter(len(columns))}{len(rows) + 1}"
        table = Table(displayName=title.replace(" ", ""), ref=ref)
        table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
        ws.add_table(table)
    ws.freeze_panes = "A2"


def _xlsx(rows: list[dict], out: Path) -> None:
    wb = Workbook()
    wb.remove(wb.active)
    _sheet(wb, "Products", rows, COLUMNS, {"title": 50, "category": 18, "url": 60, "image_url": 60, "upc": 18})
    prods = [Product(**r) for r in rows]
    _sheet(wb, "Summary", summarize(prods), list(summarize(prods)[0].keys()) if rows else ["category"], {"category": 22})
    wb.save(out)
