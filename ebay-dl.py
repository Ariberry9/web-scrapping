import argparse
import requests
import csv
import json
import time
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def price_fxn(text):
    text = text.strip().replace(",", "")
    text = text.split(" to ")[0]

    cleaned = ""
    for ch in text:
        if ch.isdigit() or ch == ".":
            cleaned += ch

    if cleaned:
        return int(float(cleaned) * 100)
    return None


def sold_fxn(text):
    text = text.strip().lower().replace(",", "")

    if "sold" not in text:
        return None

    cleaned = ""
    for ch in text:
        if ch.isdigit():
            cleaned += ch
        elif cleaned:
            break

    if cleaned:
        return int(cleaned)

    return None


def shipping_fxn(text):
    text = text.strip().lower().replace(",", "")

    if "free" in text:
        return 0

    cleaned = ""
    for ch in text:
        if ch.isdigit() or ch == ".":
            cleaned += ch

    if cleaned:
        return int(float(cleaned) * 100)

    return None


def download_html_and_run_javascript(url):
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(7000)
        html = page.content()
        browser.close()
    return html


def extract_items_from_html(html):
    soup = BeautifulSoup(html, "html.parser")

    tags = soup.select("li.s-item, li.s-card")
    print("tags =", len(tags))

    items = []

    for item_tag in tags:
        name = None
        price = None
        status = None
        shipping = None
        free_returns = None
        items_sold = None

        name_tag = item_tag.select_one(".s-item__title, .s-card__title")
        if not name_tag:
            continue

        clipped = item_tag.select_one(".clipped")
        if clipped:
            clipped.decompose()

        name = name_tag.get_text(" ", strip=True)

        if not name:
            continue
        if "shop on ebay" in name.lower():
            continue
        if "new listing" in name.lower():
            name = name.replace("New Listing", "").strip()

        price_tag = item_tag.select_one(".s-item__price, .s-card__price")
        if price_tag:
            price = price_fxn(price_tag.get_text(" ", strip=True))

        status_tag = item_tag.select_one(".SECONDARY_INFO, .s-card__subtitle-row")
        if status_tag:
            status = status_tag.get_text(" ", strip=True)

        attribute_rows = item_tag.select(
            ".s-item__shipping, .s-item__freeReturns, .s-item__hotness, .s-card__attribute-row"
        )

        for row in attribute_rows:
            row_text = row.get_text(" ", strip=True).lower()

            if "sold" in row_text:
                items_sold = sold_fxn(row_text)
            elif "free returns" in row_text:
                free_returns = True
            elif "returns" in row_text and free_returns is None:
                free_returns = False
            elif "shipping" in row_text or "delivery" in row_text or "free delivery" in row_text:
                shipping = shipping_fxn(row_text)

        items.append(
            {
                "name": name,
                "price": price,
                "status": status,
                "shipping": shipping,
                "free_returns": free_returns,
                "items_sold": items_sold,
            }
        )

    return items


def search_ebay(search_term, num_pages):
    items = []

    for page_number in range(1, num_pages + 1):
        url = "https://www.ebay.com/sch/i.html?_from=R40&_nkw="
        url += quote_plus(search_term)
        url += "&_sacat=0&LH_TitleDesc=0&_pgn="
        url += str(page_number)
        url += "&rt=nc"

        print("url =", url)

        try:
            html = download_html_and_run_javascript(url)
            page_items = extract_items_from_html(html)
            items.extend(page_items)
            time.sleep(2)
        except Exception as e:
            print(f"Failed on page {page_number}: {e}")

    return items


def main():
    parser = argparse.ArgumentParser(
        description="Download information from eBay and save as JSON or CSV."
    )
    parser.add_argument("search_term")
    parser.add_argument("--num_pages", type=int, default=10)
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Save output as CSV instead of JSON",
    )
    args = parser.parse_args()

    items = search_ebay(args.search_term, args.num_pages)

    filename_base = args.search_term.replace(" ", "_")

    if args.csv:
        filename = filename_base + ".csv"
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "name",
                    "price",
                    "status",
                    "shipping",
                    "free_returns",
                    "items_sold",
                ],
            )
            writer.writeheader()
            writer.writerows(items)
    else:
        filename = filename_base + ".json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=4, ensure_ascii=False)

    print(f"{len(items)} items saved to {filename}")


if __name__ == "__main__":
    main()