<div align="center">

# 🕷️ Catalog Scraper

**Парсер каталогу інтернет-магазину: обходить усі сторінки, відкриває картки товарів паралельно й зберігає результат в Excel, CSV або JSON.**

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Requests](https://img.shields.io/badge/requests-retry%20%2B%20backoff-orange)
![BeautifulSoup](https://img.shields.io/badge/BeautifulSoup-4-59666C)
![Tests](https://img.shields.io/badge/tests-10%20passed-2ea44f)

</div>

## Результат реального запуску

Демо-сайт [books.toscrape.com](https://books.toscrape.com) створений спеціально для практики парсингу.

```text
$ python -m scraper -o examples/books.xlsx
  сторінки товарів: 1000/1000
✓ 1000 товарів, 1050 запитів за 110.0 с → examples\books.xlsx
  Топ категорій: Default (152), Nonfiction (110), Sequential Art (75), Add a comment (67), Fiction (65)
```

Готовий файл: [`examples/books.xlsx`](examples/books.xlsx) (аркуші *Products* і *Summary*) і [`examples/books_sample.json`](examples/books_sample.json).

**Аркуш Products** (1000 рядків, 11 колонок):

| title | category | price | rating | in_stock | stock_count | upc |
|---|---|---:|---:|---|---:|---|
| A Light in the Attic | Poetry | 51.77 | 3 | True | 22 | a897fe39b1053632 |
| Tipping the Velvet | Historical Fiction | 53.74 | 1 | True | 20 | 90fa61229261140a |
| Soumission | Fiction | 50.10 | 1 | True | 20 | 6957f44c3847a760 |

**Аркуш Summary**: аналітика по категоріях:

| category | products | avg_price | min_price | max_price | avg_rating | units_in_stock |
|---|---:|---:|---:|---:|---:|---:|
| Default | 152 | 34.39 | 10.23 | 58.87 | 2.84 | 1345 |
| Nonfiction | 110 | 34.26 | 11.68 | 59.90 | 2.88 | 975 |
| Sequential Art | 75 | 34.57 | 10.16 | 57.62 | 2.97 | 686 |

## Можливості

- 📄 **Пагінація**: проходить усі сторінки каталогу за посиланням «next», захищена від зациклення
- ⚡ **Паралельність**: картки товарів завантажуються в кількох потоках (`--workers`)
- 🤝 **Ввічливість до сайту**: спільний для всіх потоків ліміт запитів (`--delay`), свій User-Agent
- 🔁 **Надійність**: повтори з експоненційною затримкою на 429/5xx, повага до `Retry-After`, таймаути. Якщо одна картка не завантажилась, товар все одно лишається в результаті
- 🧹 **Чисті дані**: ціни → числа й код валюти (`£51.77` → `51.77, GBP`, `1 299,50 грн` → `1299.5, UAH`), рейтинг → число, залишок на складі з тексту «In stock (22 available)»
- 📊 **Excel з аналітикою**: «розумні» таблиці з фільтрами, закріплений заголовок, зведення по категоріях
- ✅ **Тести без мережі** на збережених HTML-сторінках

## Встановлення і запуск

```bash
git clone https://github.com/q1mlvd/web-scraper.git
cd web-scraper
pip install -r requirements.txt

python -m scraper                              # увесь каталог → output/products.xlsx
python -m scraper --pages 3 -o books.csv       # перші 3 сторінки в CSV
python -m scraper --no-details -o fast.json    # лише дані зі списку, без карток (у 20 разів швидше)
python -m scraper --workers 16 --delay 0.05 -v # швидше й з логами
```

## Як це влаштовано

```
scraper/
├── http.py      # Session + Retry/backoff + потокобезпечний RateLimiter
├── parsers.py   # Чисті функції розбору HTML → dataclass Product (без мережі)
├── crawler.py   # Обхід пагінації + ThreadPoolExecutor для карток
├── export.py    # Excel (таблиці + Summary) / CSV / JSON
└── cli.py       # Командний рядок
```

Щоб адаптувати під інший магазин, досить змінити CSS-селектори в `parsers.py`. Мережа, паралельність, повтори й експорт лишаються без змін.

## Тести

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Технології

`Python` · `requests` · `urllib3 Retry` · `BeautifulSoup4` · `concurrent.futures` · `openpyxl` · `pytest` · `GitHub Actions`
