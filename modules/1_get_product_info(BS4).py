import re
from decimal import Decimal, InvalidOperation
from pprint import pprint

import requests
from bs4 import BeautifulSoup

from load_django import *
from parser_app.models import Product


def clean_price(price_str):
    if price_str:
        try:
            price_digits = "".join(re.findall(r"\d+", price_str))
            if price_digits:
                return Decimal(price_digits)
        except (InvalidOperation, ValueError):
            return None
    return None


def clean_memory(memory_str):
    if memory_str:
        match = re.search(r"\d+", memory_str)
        if match:
            return int(match.group(0))
    return None


def clean_diagonal(diagonal_str):
    if diagonal_str:
        match = re.search(r"[\d.]+", diagonal_str)
        if match:
            return float(match.group(0))
    return None


url = "https://brain.com.ua/ukr/Mobilniy_telefon_Apple_iPhone_16_Pro_Max_256GB_Black_Titanium-p1145443.html"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:147.0) Gecko/20100101 Firefox/147.0",
    "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}

try:
    r = requests.get(url, headers=headers)
    r.raise_for_status()
except requests.RequestException as e:
    print(f"Error fetching URL: {e}")

soup = BeautifulSoup(r.text, "html.parser")
product_data = {}

try:
    product_data["name"] = soup.h1.text.strip()
except AttributeError:
    product_data["name"] = None

try:
    product_data["color"] = soup.find("span", string="Колір").find_next_sibling("span").text.strip()
except AttributeError:
    product_data["color"] = None

try:
    memory_raw = soup.find("span", string="Вбудована пам'ять").find_next_sibling("span").text.strip()
    product_data["memory"] = clean_memory(memory_raw)
except AttributeError:
    product_data["memory"] = None

try:
    product_data["vendor"] = soup.find("span", string="Виробник").find_next_sibling("span").text.strip()
except AttributeError:
    product_data["vendor"] = None

try:
    price_raw = soup.find("div", class_="price-wrapper").find("span", class_="").text.strip()
    product_data["price"] = clean_price(price_raw)
except AttributeError:
    product_data["price"] = None

try:
    price_promo_raw = soup.find("span", class_="red-price").text.strip()
    product_data["price_promo"] = clean_price(price_promo_raw)
except AttributeError:
    product_data["price_promo"] = None

try:
    container = soup.find("div", class_=re.compile("main-pictures-block"))
    product_data["images"] = [img["src"] for img in container.find_all("img")]
except AttributeError:
    product_data["images"] = []

try:
    product_data["sku"] = soup.find("span", class_="br-pr-code-val").text.strip()
except AttributeError:
    product_data["sku"] = None

try:
    revs_count_raw = soup.find("a", class_=re.compile("reviews-count")).span.text.strip()
    product_data["revs_count"] = int(revs_count_raw) if revs_count_raw.isdigit() else None
except (AttributeError, ValueError):
    product_data["revs_count"] = None

try:
    diagonal_raw = soup.find("span", string="Діагональ екрану").find_next_sibling("span").text.strip()
    product_data["diagonal"] = clean_diagonal(diagonal_raw)
except AttributeError:
    product_data["diagonal"] = None

try:
    product_data["resolution"] = soup.find("span", string="Роздільна здатність екрану").find_next_sibling("span").text.strip()
except AttributeError:
    product_data["resolution"] = None

specifications = {}
try:
    container = soup.find_all("div", class_="br-pr-chr-item")
    for spec_items in container:
        specs = spec_items.div.find_all("div")
        for item in specs:
            spans = item.find_all("span")
            if len(spans) >= 2:
                key = spans[0].text.strip()
                value = spans[1].text.strip()
                if key and value:
                    specifications[key] = value
except AttributeError:
    pass

product_data["specifications"] = specifications

pprint(product_data)

product, created = Product.objects.get_or_create(**product_data)
