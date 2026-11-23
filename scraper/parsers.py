"""Pure HTML parsing functions (no network), easy to unit-test with saved pages."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


@dataclass
class Product:
    title: str
    url: str
    price: float
    currency: str
    rating: int
    in_stock: bool
    stock_count: Optional[int] = None
    category: Optional[str] = None
    upc: Optional[str] = None
    reviews: Optional[int] = None
    image_url: Optional[str] = None
    description: Optional[str] = field(default=None, repr=False)

    def to_dict(self) -> dict:
        return asdict(self)


def parse_price(text: str) -> tuple[float, str]:
    """'£51.77' -> (51.77, 'GBP'). Handles spaces and comma decimals: '1 299,00 грн' -> (1299.0, 'UAH')."""
    symbols = {"£": "GBP", "$": "USD", "€": "EUR", "₴": "UAH", "грн": "UAH"}
    currency = next((code for sym, code in symbols.items() if sym in text), "")
    number = re.sub(r"[^\d,.\-]", "", text)
    if "," in number and "." not in number:
        number = number.replace(",", ".")
    number = number.replace(",", "")
    return float(number), currency


def parse_rating(tag) -> int:
    classes = tag.get("class", []) if tag else []
    return next((RATINGS[c] for c in classes if c in RATINGS), 0)


def parse_list_page(html: str, page_url: str) -> tuple[list[Product], Optional[str]]:
    """Return the products on a catalogue page and the absolute URL of the next page (or None)."""
    soup = BeautifulSoup(html, "html.parser")
    products = []
    for pod in soup.select("article.product_pod"):
        link = pod.select_one("h3 a")
        price, currency = parse_price(pod.select_one(".price_color").get_text(strip=True))
        img = pod.select_one("img")
        products.append(
            Product(
                title=link["title"].strip(),
                url=urljoin(page_url, link["href"]),
                price=price,
                currency=currency,
                rating=parse_rating(pod.select_one(".star-rating")),
                in_stock="in stock" in pod.select_one(".availability").get_text(" ", strip=True).lower(),
                image_url=urljoin(page_url, img["src"]) if img else None,
            )
        )
    nxt = soup.select_one("li.next a")
    return products, (urljoin(page_url, nxt["href"]) if nxt else None)


def parse_product_page(html: str, product: Product) -> Product:
    """Fill in the details that exist only on the product page."""
    soup = BeautifulSoup(html, "html.parser")
    table = {th.get_text(strip=True): td.get_text(strip=True) for th, td in
             ((row.th, row.td) for row in soup.select("table.table-striped tr")) if th and td}
    crumbs = [a.get_text(strip=True) for a in soup.select("ul.breadcrumb li a")]
    availability = soup.select_one(".product_main .availability")
    stock = re.search(r"(\d+)\s+available", availability.get_text(" ", strip=True)) if availability else None
    desc = soup.select_one("#product_description + p")

    product.upc = table.get("UPC")
    product.reviews = int(table["Number of reviews"]) if table.get("Number of reviews", "").isdigit() else None
    product.stock_count = int(stock.group(1)) if stock else (0 if not product.in_stock else None)
    product.category = crumbs[-1] if len(crumbs) >= 3 else None
    product.description = desc.get_text(strip=True) if desc else None
    return product
