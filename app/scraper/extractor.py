import json
import re

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}


def parse_price(raw_price: str | int | float) -> float | None:
    if isinstance(raw_price, (int, float)):
        return float(raw_price) if raw_price > 0 else None

    cleaned = re.sub(r"[^\d.,]", "", str(raw_price).strip())
    if not cleaned:
        return None

    # Formato colombiano/europeo con puntos de miles (ej: 1.299.000 o 1.299.000,50)
    if "." in cleaned and "," in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "." in cleaned:
        parts = cleaned.split(".")
        if len(parts[-1]) == 3:
            cleaned = cleaned.replace(".", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) == 3:
            cleaned = cleaned.replace(",", "")
        else:
            cleaned = cleaned.replace(",", ".")

    try:
        value = float(cleaned)
        return value if value > 0 else None
    except ValueError:
        return None


def _extract_from_json_ld(soup: BeautifulSoup) -> float | None:
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            offers = item.get("offers")
            if isinstance(offers, list) and offers:
                offers = offers[0]
            if isinstance(offers, dict):
                raw_price = offers.get("price") or offers.get("lowPrice")
                if raw_price is not None:
                    price = parse_price(raw_price)
                    if price:
                        return price
    return None


def _extract_from_meta_or_html(soup: BeautifulSoup) -> float | None:
    meta_selectors = [
        ("meta", {"property": "product:price:amount"}),
        ("meta", {"itemprop": "price"}),
        ("meta", {"name": "twitter:data1"}),
    ]
    for tag, attrs in meta_selectors:
        element = soup.find(tag, attrs=attrs)
        if element and element.get("content"):
            price = parse_price(element["content"])
            if price:
                return price

    css_selectors = [
        "#js-original_price",
        "[itemprop='price']",
        ".new-price",
        ".price-alkomprar",
    ]
    for selector in css_selectors:
        element = soup.select_one(selector)
        if element:
            raw = element.get("content") or element.get_text()
            price = parse_price(raw)
            if price:
                return price

    return None


def fetch_price(url: str) -> float:
    with httpx.Client(
        headers=HEADERS, follow_redirects=True, timeout=15.0
    ) as client:
        response = client.get(url)
        response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    price = _extract_from_json_ld(soup) or _extract_from_meta_or_html(soup)
    if price is None:
        raise ValueError(f"No se pudo extraer el precio desde: {url}")

    return price
