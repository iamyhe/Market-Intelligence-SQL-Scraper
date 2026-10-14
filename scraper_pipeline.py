"""
MarketPulse AI - Automated Web Scraping & Relational SQL Database Pipeline
===========================================================================
Scrapes e-commerce catalog data, cleans and enriches pricing metrics,
and loads normalized records into a relational SQLite database.
"""

import re
import sqlite3
import sys
from datetime import datetime
import numpy as np
import requests
from bs4 import BeautifulSoup

# Ensure smooth terminal output on Windows PowerShell
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "https://books.toscrape.com/"
DB_NAME = "market_intelligence.db"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


def fetch_categories(session: requests.Session) -> list[tuple[str, str]]:
    """Scrapes category names and URLs from the target e-commerce homepage."""
    resp = session.get(BASE_URL, timeout=12)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    categories = []
    nav_list = soup.select("div.side_categories ul.nav-list li ul li a")
    for link in nav_list:
        cat_name = link.get_text(strip=True)
        cat_href = link.get("href", "")
        if cat_name and cat_name not in ("Books", "Default", "Add a comment"):
            full_url = BASE_URL + cat_href.lstrip("/")
            categories.append((cat_name, full_url))
    return categories[:15]  # Top 15 distinct categories for a rich, fast dataset


def scrape_category_products(
    session: requests.Session, category_name: str, category_url: str, rng: np.random.Generator
) -> list[dict]:
    """Scrapes all products listed on a category page and computes competitive metrics."""
    products = []
    resp = session.get(category_url, timeout=12)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    articles = soup.select("article.product_pod")
    for idx, item in enumerate(articles, start=1):
        # 1. Product Title
        title_tag = item.select_one("h3 a")
        title = title_tag.get("title", title_tag.get_text(strip=True)) if title_tag else f"{category_name} Item {idx}"

        # 2. Price Cleaning (£ -> float)
        price_tag = item.select_one("p.price_color")
        raw_price = price_tag.get_text(strip=True) if price_tag else "25.00"
        cleaned_price_str = re.sub(r"[^0-9.]", "", raw_price)
        our_price = round(float(cleaned_price_str) if cleaned_price_str else 25.0, 2)

        # 3. Star Rating (Word -> Integer 1-5)
        rating_tag = item.select_one("p.star-rating")
        rating_classes = rating_tag.get("class", []) if rating_tag else []
        rating_word = next((c for c in rating_classes if c in RATING_MAP), "Three")
        rating = RATING_MAP.get(rating_word, 3)

        # 4. Competitive Market Simulation (Realistic E-Commerce Intelligence)
        market_multiplier = rng.normal(loc=1.02, scale=0.12)
        market_multiplier = float(np.clip(market_multiplier, 0.78, 1.32))
        competitor_price = round(our_price * market_multiplier, 2)

        # Price Difference %: positive means our price is higher than competitor
        price_diff_pct = round(((our_price - competitor_price) / competitor_price) * 100, 2)

        if price_diff_pct < -3.0:
            price_status = "Undercutting (Cheaper)"
        elif price_diff_pct > 3.0:
            price_status = "Overpriced (At Risk)"
        else:
            price_status = "Price Match (Competitive)"

        # 5. Inventory & Demand Estimation
        stock_quantity = int(rng.integers(3, 65))
        base_demand = 45 + (rating * 18) - (our_price * 0.45) - (price_diff_pct * 1.1)
        est_monthly_sales = int(max(5, round(base_demand + rng.normal(0, 8))))
        est_monthly_revenue = round(our_price * est_monthly_sales, 2)

        products.append(
            {
                "title": title,
                "category_name": category_name,
                "our_price": our_price,
                "competitor_price": competitor_price,
                "price_diff_pct": price_diff_pct,
                "price_status": price_status,
                "rating": rating,
                "stock_quantity": stock_quantity,
                "est_monthly_sales": est_monthly_sales,
                "est_monthly_revenue": est_monthly_revenue,
            }
        )
    return products


def generate_fallback_dataset(rng: np.random.Generator) -> list[dict]:
    """Deterministic fallback generator in case of offline environment or firewall."""
    sample_categories = [
        "Travel", "Mystery", "Sequential Art", "Science Fiction",
        "Business", "Philosophy", "Poetry", "History", "Science", "Art"
    ]
    products = []
    for cat in sample_categories:
        for i in range(1, 26):
            our_price = round(float(rng.uniform(12.5, 59.99)), 2)
            comp_price = round(our_price * float(rng.uniform(0.82, 1.25)), 2)
            diff_pct = round(((our_price - comp_price) / comp_price) * 100, 2)
            status = (
                "Undercutting (Cheaper)" if diff_pct < -3.0
                else ("Overpriced (At Risk)" if diff_pct > 3.0 else "Price Match (Competitive)")
            )
            rating = int(rng.integers(1, 6))
            stock = int(rng.integers(4, 60))
            sales = int(max(8, round(50 + rating * 15 - our_price * 0.4 - diff_pct)))
            products.append(
                {
                    "title": f"{cat} Edition Vol. {i}: Market Series",
                    "category_name": cat,
                    "our_price": our_price,
                    "competitor_price": comp_price,
                    "price_diff_pct": diff_pct,
                    "price_status": status,
                    "rating": rating,
                    "stock_quantity": stock,
                    "est_monthly_sales": sales,
                    "est_monthly_revenue": round(our_price * sales, 2),
                }
            )
    return products


def build_sql_database(products: list[dict], db_path: str = DB_NAME) -> None:
    """Creates a normalized relational SQLite database with categories and products tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("DROP TABLE IF EXISTS products;")
    cursor.execute("DROP TABLE IF EXISTS categories;")

    # 1. Create Dimension Table: categories
    cursor.execute(
        """
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE NOT NULL,
            target_margin_pct REAL NOT NULL
        );
        """
    )

    # 2. Create Fact Table: products
    cursor.execute(
        """
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            our_price REAL NOT NULL,
            competitor_price REAL NOT NULL,
            price_diff_pct REAL NOT NULL,
            price_status TEXT NOT NULL,
            rating INTEGER NOT NULL,
            stock_quantity INTEGER NOT NULL,
            est_monthly_sales INTEGER NOT NULL,
            est_monthly_revenue REAL NOT NULL,
            scraped_at TEXT NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories (category_id)
        );
        """
    )

    rng = np.random.default_rng(42)
    unique_cats = sorted({p["category_name"] for p in products})
    for cat_name in unique_cats:
        margin = round(float(rng.uniform(22.0, 42.0)), 1)
        cursor.execute(
            "INSERT INTO categories (category_name, target_margin_pct) VALUES (?, ?);",
            (cat_name, margin),
        )

    cursor.execute("SELECT category_name, category_id FROM categories;")
    cat_id_map = dict(cursor.fetchall())

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for idx, p in enumerate(products, start=1):
        sku = f"MP-{idx:04d}"
        cursor.execute(
            """
            INSERT INTO products (
                sku, title, category_id, our_price, competitor_price,
                price_diff_pct, price_status, rating, stock_quantity,
                est_monthly_sales, est_monthly_revenue, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                sku,
                p["title"],
                cat_id_map[p["category_name"]],
                p["our_price"],
                p["competitor_price"],
                p["price_diff_pct"],
                p["price_status"],
                p["rating"],
                p["stock_quantity"],
                p["est_monthly_sales"],
                p["est_monthly_revenue"],
                timestamp,
            ),
        )

    conn.commit()
    conn.close()


def run_verification_queries(db_path: str = DB_NAME) -> None:
    """Runs analytical SQL queries (JOIN, GROUP BY, ORDER BY) and prints results."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n" + "=" * 68)
    print("  SQL DATABASE VERIFICATION & ANALYTICAL QUERIES")
    print("=" * 68)

    # Query 1: Category Revenue & Pricing Summary (INNER JOIN + GROUP BY)
    q1 = """
    SELECT 
        c.category_name,
        COUNT(p.product_id) AS total_items,
        ROUND(AVG(p.our_price), 2) AS avg_our_price,
        ROUND(AVG(p.competitor_price), 2) AS avg_comp_price,
        ROUND(SUM(p.est_monthly_revenue), 2) AS total_revenue
    FROM products p
    INNER JOIN categories c ON p.category_id = c.category_id
    GROUP BY c.category_name
    ORDER BY total_revenue DESC
    LIMIT 6;
    """
    print("\n[SQL Query 1] Top 6 Categories by Estimated Monthly Revenue (JOIN + GROUP BY):")
    print(f"  {'Category':<20} | {'Items':<6} | {'Our Avg $':<10} | {'Comp Avg $':<10} | {'Est. Revenue':<12}")
    print("  " + "-" * 66)
    for row in cursor.execute(q1):
        print(f"  {row[0]:<20} | {row[1]:<6} | ${row[2]:<9.2f} | ${row[3]:<9.2f} | ${row[4]:,.2f}")

    # Query 2: Pricing Positioning Breakdown
    q2 = """
    SELECT 
        price_status,
        COUNT(*) AS product_count,
        ROUND(AVG(price_diff_pct), 2) AS avg_diff_pct,
        ROUND(SUM(est_monthly_revenue), 2) AS revenue_exposure
    FROM products
    GROUP BY price_status
    ORDER BY product_count DESC;
    """
    print("\n[SQL Query 2] Competitive Price Positioning Breakdown:")
    print(f"  {'Positioning Status':<28} | {'Count':<6} | {'Avg Diff %':<10} | {'Revenue Exposure':<15}")
    print("  " + "-" * 66)
    for row in cursor.execute(q2):
        print(f"  {row[0]:<28} | {row[1]:<6} | {row[2]:>+8.2f}%  | ${row[3]:,.2f}")

    conn.close()


def main():
    print("MARKETPULSE AI - Web Scraping & SQL Database Pipeline")
    print("=" * 68)

    rng = np.random.default_rng(42)
    all_products = []

    try:
        with requests.Session() as session:
            session.headers.update({"User-Agent": "Mozilla/5.0 (MarketPulseDataBot/1.0)"})
            print("[>>] Connecting to target e-commerce store (books.toscrape.com)...")
            categories = fetch_categories(session)
            print(f"[OK] Discovered {len(categories)} product categories to scrape.")

            for cat_name, cat_url in categories:
                items = scrape_category_products(session, cat_name, cat_url, rng)
                all_products.extend(items)
                print(f"  + Scraped category '{cat_name:<18}' -> {len(items):>2} products extracted")
    except Exception as exc:
        print(f"[WARN] Live scraping interrupted ({exc}). Activating deterministic fallback...")
        all_products = generate_fallback_dataset(rng)

    print("-" * 68)
    print(f"[OK] Total products extracted & cleaned: {len(all_products)} records")
    print(f"[>>] Building relational SQLite database -> {DB_NAME} ...")

    build_sql_database(all_products, DB_NAME)
    print("[OK] Created table 'categories' (Primary Key: category_id)")
    print("[OK] Created table 'products'   (Foreign Key: category_id -> categories)")

    run_verification_queries(DB_NAME)

    print("\n" + "=" * 68)
    print(f"[SUCCESS] Pipeline complete! Database saved to '{DB_NAME}'")
    print("=" * 68)


if __name__ == "__main__":
    main()