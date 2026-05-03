#!/usr/bin/env python3
"""
Разовый парсер запчастей по артикулам.
exist.ru + emex.ru + autopiter.ru → prices.xlsx
"""
#!/usr/bin/env python3
import time, re, datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait          # ← новое
from selenium.webdriver.support import expected_conditions as EC # ← новое
import pandas as pd

ARTICLES = [
    "S18D6300010DY", "S18D2803501DQ", "S18D2804501DQ",
    "S18D2804523",   "670020R141",   "S18D3773010",
    "S18D3773020",   "S18D2804800DY", "S18D5600010DY"
]

SITES = {
    "idriver": {
        "url": "https://idriver.by",   # главная страница
        "search_box": "input[name='keyword']",  # поле поиска
        "row_sel": "div.product-item",          # карточка товара
        "price_sel": "span.price",
        "brand_sel": "div.brand",
        "stock_sel": "div.availability"
    },
    "exist": {
        "url_tpl": "https://exist.ru/Price/?pcode={}",
        "price_sel": 'span[data-field="price"]',
        "stock_sel": 'span[data-field="ship"]',
        "brand_sel": 'span[data-field="brand"]'
    },
    "emex": {
        "url_tpl": "https://emex.ru/f?detailNum={}&makeId=",
        "price_sel": '.price-actual',
        "stock_sel": '.availability-text',
        "brand_sel": '.brand-name'
    },
    "autopiter": {
        "url_tpl": "https://autopiter.ru/goods/Search?code={}",
        "price_sel": '.price-value',
        "stock_sel": '.stock-info',
        "brand_sel": '.brand-title'
    }
}

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def parse_site(driver, site_key, art):
    cfg = SITES[site_key]
    price = stock = brand = None
    try:
        if site_key == "idriver":
            driver.get(cfg["url"])
            search = driver.find_element(By.CSS_SELECTOR, cfg["search_box"])
            search.clear()
            search.send_keys(art)
            search.send_keys("\ue007")          # Enter
            time.sleep(3)
            rows = driver.find_elements(By.CSS_SELECTOR, cfg["row_sel"])
            if rows:
                price = rows[0].find_element(By.CSS_SELECTOR, cfg["price_sel"]).text
                stock = rows[0].find_element(By.CSS_SELECTOR, cfg["stock_sel"]).text
                brand = rows[0].find_element(By.CSS_SELECTOR, cfg["brand_sel"]).text

        elif site_key == "exist":
            driver.get(cfg["url_tpl"].format(art))
            time.sleep(3)
            row = driver.find_elements(By.CSS_SELECTOR, "table.offers-table tbody tr")
            if row:
                price = row[0].find_element(By.CSS_SELECTOR, "span[data-field='price']").text
                stock = row[0].find_element(By.CSS_SELECTOR, "span[data-field='ship']").text
                brand = row[0].find_element(By.CSS_SELECTOR, "span[data-field='brand']").text

        elif site_key == "emex":
            driver.get(cfg["url_tpl"].format(art))
            time.sleep(3)
            price = driver.find_element(By.CSS_SELECTOR, ".price-actual").text
            stock = driver.find_element(By.CSS_SELECTOR, ".availability-text").text
            brand = driver.find_element(By.CSS_SELECTOR, ".brand-name").text

        elif site_key == "autopiter":
            driver.get(cfg["url_tpl"].format(art))
            time.sleep(3)
            price = driver.find_element(By.CSS_SELECTOR, ".price-value").text
            stock = driver.find_element(By.CSS_SELECTOR, ".stock-info").text
            brand = driver.find_element(By.CSS_SELECTOR, ".brand-title").text

    except Exception as e:
        print(f"    {site_key}: элемент не найден ({e.__class__.__name__})")

    if price:
        price = re.sub(r"\D", "", price)
        price = int(price) if price else None

    return {"артикул": art, "сайт": site_key, "цена": price,
            "наличие": stock, "бренд": brand, "ссылка": driver.current_url,
            "срок поставки": None}

def main():
    driver = init_driver()
    rows = []
    for art in ARTICLES:
        print("ищу", art)
        for site in SITES:
            try:
                row = parse_site(driver, site, art)
                rows.append(row)
            except Exception as e:
                print("  ошибка", site, e)
    driver.quit()

    df = pd.DataFrame(rows)
    file_name = f"prices_{datetime.date.today().isoformat()}.xlsx"
    df.to_excel(file_name, index=False)
    print("готово →", file_name)

if __name__ == "__main__":
    main()