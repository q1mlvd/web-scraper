"""Walk the catalogue pagination, then fetch product pages in parallel."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

import requests

from .http import Fetcher
from .parsers import Product, parse_list_page, parse_product_page

log = logging.getLogger("scraper")

DEFAULT_START = "https://books.toscrape.com/catalogue/page-1.html"


def crawl(
    start_url: str = DEFAULT_START,
    fetcher: Optional[Fetcher] = None,
    max_pages: Optional[int] = None,
    details: bool = True,
    workers: int = 8,
    progress: Callable[[int, int], None] | None = None,
) -> list[Product]:
    fetcher = fetcher or Fetcher()
    products: list[Product] = []
    seen: set[str] = set()
    url: Optional[str] = start_url
    pages = 0

    while url and (max_pages is None or pages < max_pages):
        if url in seen:  # protects against pagination loops
            break
        seen.add(url)
        items, url = parse_list_page(fetcher.get(url), url)
        products.extend(items)
        pages += 1
        log.info("page %d: %d products (total %d)", pages, len(items), len(products))

    if details and products:
        done = 0

        def fill(p: Product) -> Product:
            return parse_product_page(fetcher.get(p.url), p)

        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(fill, p): p for p in products}
            for fut in as_completed(futures):
                try:
                    fut.result()
                except requests.RequestException as e:  # keep the list item even if its page failed
                    log.warning("details failed for %s: %s", futures[fut].url, e)
                done += 1
                if progress:
                    progress(done, len(products))
    return products
