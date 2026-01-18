import re
from decimal import Decimal, InvalidOperation
from pprint import pprint

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, InvalidSessionIdException
from selenium.webdriver.common.keys import Keys

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


def get_clean_text_selenium(driver, by_type, selector):
    try:
        element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((by_type, selector))
        )
        return element.get_attribute("textContent").strip()
    except TimeoutException:
        return None


def run():
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get("https://brain.com.ua/")

    try:
        search_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".header-bottom input.quick-search-input"))
        )
        search_input.clear()
        search_input.send_keys("Apple iPhone 15" + Keys.ENTER)
    except (TimeoutException, InvalidSessionIdException):
        print("Search field not found")
        return

    try:
        product_locator = (By.CSS_SELECTOR, ".product-wrapper")
        WebDriverWait(driver, 5).until(EC.presence_of_element_located(product_locator))

        product = driver.find_element(*product_locator)
        link = product.find_element(By.TAG_NAME, "a")
        prod_url = link.get_attribute("href")
        driver.get(prod_url)
    except TimeoutException:
        print("Search results did not load.")
        return

    product_data = {}

    product_data["name"] = get_clean_text_selenium(driver, By.XPATH, "//h1[contains(@class, 'desktop')]")
    product_data["color"] = get_clean_text_selenium(driver, By.XPATH, '//span[contains(text(), "Колір")]/following-sibling::span')

    memory_raw = get_clean_text_selenium(driver, By.XPATH, '''//span[contains(text(), "Вбудована пам'ять")]/following-sibling::span''')
    product_data["memory"] = clean_memory(memory_raw)

    product_data["vendor"] = get_clean_text_selenium(driver, By.XPATH, '//span[contains(text(), "Виробник")]/following-sibling::span')

    price_raw = get_clean_text_selenium(driver, By.XPATH, '//div[contains(@class, "price-wrapper")]/span')
    product_data["price"] = clean_price(price_raw)

    price_promo_raw = get_clean_text_selenium(driver, By.XPATH, '//span[contains(@class, "red-price")]')
    product_data["price_promo"] = clean_price(price_promo_raw)

    images_elements = driver.find_elements(By.XPATH, '//div[contains(@class, "main-pictures-block")]//img')
    product_data["images"] = [img.get_attribute("src") for img in images_elements]

    product_data["sku"] = get_clean_text_selenium(driver, By.XPATH, '//span[contains(@class, "br-pr-code-val")]')

    revs_count_raw = get_clean_text_selenium(driver, By.XPATH, '//a[contains(@class, "reviews-count")]//span')
    product_data["revs_count"] = int(revs_count_raw) if revs_count_raw.isdigit() else None

    diagonal_raw = get_clean_text_selenium(driver, By.XPATH, '''//span[contains(text(), "Діагональ екрану")]/following-sibling::span''')
    product_data["diagonal"] = clean_diagonal(diagonal_raw)

    product_data["resolution"] = get_clean_text_selenium(driver, By.XPATH, '''//span[contains(text(), "Роздільна здатність екрану")]/following-sibling::span''')

    specifications = {}

    specs = driver.find_elements(By.XPATH, '//div[contains(@class, "br-pr-chr-item")]//div[count(span) >= 2]')
    for spec in specs:
        try:
            items = spec.find_elements(By.TAG_NAME,"span")
            key = items[0].get_attribute("textContent").strip()
            value = items[1].get_attribute("textContent").strip()
            if key and value:
                specifications[key] = value
        except IndexError:
            continue

    product_data["specifications"] = specifications

    driver.quit()

    pprint(product_data)

    product, created = Product.objects.get_or_create(**product_data)


run()