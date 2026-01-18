import re
from decimal import Decimal, InvalidOperation
from pprint import pprint

from playwright.sync_api import sync_playwright, Locator

from load_django import *
from parser_app.models import Product


def clean_price(price_str: str):
    if price_str:
        try:
            price_digits = "".join(re.findall(r"\d+", price_str))
            if price_digits:
                return Decimal(price_digits)
        except (InvalidOperation, ValueError):
            return None
    return None


def clean_memory(memory_str: str):
    if memory_str:
        match = re.search(r"\d+", memory_str)
        if match:
            return int(match.group(0))
    return None


def clean_diagonal(diagonal_str: str):
    if diagonal_str:
        match = re.search(r"[\d.]+", diagonal_str)
        if match:
            return float(match.group(0))
    return None


def get_clean_text(locator: Locator):
    if locator.count():
        text = locator.first.inner_text().strip()
        return text if text else None
    return None


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("https://brain.com.ua/")
        page.wait_for_load_state("load")

        search_input = page.get_by_role("searchbox", name="Знайти")
        search_input.fill("Apple iPhone 15")
        search_input.press("Enter")
        page.wait_for_load_state("load")

        product = page.locator(".product-wrapper").first
        link = product.locator("a").first
        prod_url = link.get_attribute("href")

        page.goto(prod_url)
        page.wait_for_load_state("load")

        product_data = {}

        product_data["name"] = get_clean_text(page.locator("h1.main-title"))
        product_data["color"] = get_clean_text(page.locator('//span[contains(text(), "Колір")]/following-sibling::span'))

        memory_raw = get_clean_text(page.locator('''//span[contains(text(), "Вбудована пам'ять")]/following-sibling::span'''))
        product_data["memory"] = clean_memory(memory_raw)

        product_data["vendor"] = get_clean_text(page.locator('//span[contains(text(), "Виробник")]/following-sibling::span'))

        price_raw = get_clean_text(page.locator("div.price-wrapper").locator("span"))
        product_data["price"] = clean_price(price_raw)

        price_promo_raw = get_clean_text(page.locator("span.red-price"))
        product_data["price_promo"] = clean_price(price_promo_raw)

        images_container = page.locator('div[class*="main-pictures-block"]')
        if images_container.count():
            images_container = images_container.first
            images = images_container.locator("img").all()
            product_data["images"] = [img.get_attribute("src") for img in images]
        else:
            product_data["images"] = []

        product_data["sku"] = get_clean_text(page.locator("span.br-pr-code-val"))

        revs_count_raw = get_clean_text(page.locator("a.reviews-count").locator("span"))
        product_data["revs_count"] = int(revs_count_raw) if revs_count_raw.isdigit() else None

        diagonal_raw = get_clean_text(page.locator('''//span[contains(text(), "Діагональ екрану")]/following-sibling::span'''))
        product_data["diagonal"] = clean_diagonal(diagonal_raw)

        product_data["resolution"] = get_clean_text(page.locator('''//span[contains(text(), "Роздільна здатність екрану")]/following-sibling::span'''))

        specifications = {}

        specs_container = page.locator("div.br-pr-chr-item").all()
        for specs_item in specs_container:
            specs = specs_item.locator("div").locator("div").all()
            for item in specs:
                spans = item.locator("span").all()
                if len(spans) >= 2:
                    key = get_clean_text(spans[0])
                    value = get_clean_text(spans[1])
                    if key and value:
                        specifications[key] = value

        product_data["specifications"] = specifications

        browser.close()

    pprint(product_data)

    product, created = Product.objects.get_or_create(**product_data)


run()