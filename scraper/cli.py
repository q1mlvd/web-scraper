"""python -m scraper -o books.xlsx --pages 5"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

from . import __version__
from .crawler import DEFAULT_START, crawl
from .export import save, summarize
from .http import Fetcher


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(prog="scraper", description="Збирає товари з каталогу інтернет-магазину в Excel / CSV / JSON.")
    p.add_argument("-o", "--out", type=Path, default=Path("output/products.xlsx"), help="Файл результату (.xlsx/.csv/.json)")
    p.add_argument("--start", default=DEFAULT_START, help="Перша сторінка каталогу")
    p.add_argument("--pages", type=int, help="Обмежити кількість сторінок каталогу")
    p.add_argument("--no-details", action="store_true", help="Не відкривати сторінки товарів (швидше, менше полів)")
    p.add_argument("--workers", type=int, default=8, help="Паралельних потоків для сторінок товарів")
    p.add_argument("--delay", type=float, default=0.1, help="Мінімальна пауза між запитами, с")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = p.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")
    fetcher = Fetcher(delay=args.delay)
    t0 = time.perf_counter()

    def progress(done: int, total: int) -> None:
        if done == total or done % 25 == 0:
            print(f"\r  сторінки товарів: {done}/{total}", end="" if done < total else "\n", flush=True)

    products = crawl(args.start, fetcher, max_pages=args.pages, details=not args.no_details,
                     workers=args.workers, progress=progress)
    if not products:
        print("Товарів не знайдено", file=sys.stderr)
        return 1
    save(products, args.out)
    took = time.perf_counter() - t0
    print(f"✓ {len(products)} товарів, {fetcher.requests_made} запитів за {took:.1f} с → {args.out}")
    top = summarize(products)[:5]
    if top and top[0]["category"] != "—":
        print("  Топ категорій: " + ", ".join(f"{r['category']} ({r['products']})" for r in top))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
