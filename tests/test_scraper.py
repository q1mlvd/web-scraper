"""Offline tests on saved pages from books.toscrape.com."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from openpyxl import load_workbook

from scraper import crawler, export, parsers

FIX = Path(__file__).parent / "fixtures"
BASE = "https://books.toscrape.com/catalogue/"


def html(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("text, expected", [
    ("£51.77", (51.77, "GBP")),
    ("$1,299.00", (1299.0, "USD")),
    ("1 299,50 грн", (1299.5, "UAH")),
    ("€ 7", (7.0, "EUR")),
])
def test_parse_price(text, expected):
    assert parsers.parse_price(text) == expected


def test_list_page():
    products, nxt = parsers.parse_list_page(html("list_page.html"), BASE + "page-1.html")
    assert len(products) == 20
    first = products[0]
    assert first.title == "A Light in the Attic"  # full title from the title attribute, not the truncated text
    assert first.url == BASE + "a-light-in-the-attic_1000/index.html"
    assert (first.price, first.currency, first.rating, first.in_stock) == (51.77, "GBP", 3, True)
    assert nxt == BASE + "page-2.html"


def test_last_page_has_no_next():
    _, nxt = parsers.parse_list_page(html("last_page.html"), BASE + "page-50.html")
    assert nxt is None


def test_product_page_details():
    p, _ = parsers.parse_list_page(html("list_page.html"), BASE + "page-1.html")
    item = parsers.parse_product_page(html("book_page.html"), p[0])
    assert item.upc == "a897fe39b1053632"
    assert item.stock_count == 22
    assert item.category == "Poetry"
    assert item.reviews == 0
    assert item.description.startswith("It's hard to imagine")


class FakeFetcher:
    """Serves fixtures instead of the network: page-1 links to page-2, which is the last page."""

    def __init__(self):
        self.requests_made = 0

    def get(self, url: str) -> str:
        self.requests_made += 1
        if url.endswith("page-1.html"):
            return html("list_page.html")
        if url.endswith("page-2.html"):
            return html("last_page.html")
        return html("book_page.html")


def test_crawl_follows_pagination_and_fetches_details():
    f = FakeFetcher()
    products = crawler.crawl(BASE + "page-1.html", fetcher=f, workers=4)
    assert len(products) == 40
    assert f.requests_made == 2 + 40
    assert all(p.upc == "a897fe39b1053632" for p in products)


def test_crawl_respects_max_pages_and_no_details():
    f = FakeFetcher()
    products = crawler.crawl(BASE + "page-1.html", fetcher=f, max_pages=1, details=False)
    assert len(products) == 20 and f.requests_made == 1 and products[0].upc is None


def test_export_formats(tmp_path):
    products = crawler.crawl(BASE + "page-1.html", fetcher=FakeFetcher(), max_pages=1)
    assert json.loads(export.save(products, tmp_path / "a.json").read_text(encoding="utf-8"))[0]["upc"]
    assert export.save(products, tmp_path / "a.csv").read_text(encoding="utf-8-sig").startswith("title,category,price")
    wb = load_workbook(export.save(products, tmp_path / "a.xlsx"))
    assert wb.sheetnames == ["Products", "Summary"]
    assert wb["Products"].max_row == 21
    assert wb["Summary"]["A2"].value == "Poetry"
    with pytest.raises(ValueError):
        export.save(products, tmp_path / "a.txt")
